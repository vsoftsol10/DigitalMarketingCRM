import requests

from django.core import signing
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError

from apps.integrations.instagram.crypto import decrypt_token as decrypt_instagram_token
from apps.integrations.instagram.exceptions import (
    InstagramAPIError,
    InstagramIntegrationError,
    InstagramOAuthConfigurationError,
)
from apps.integrations.instagram.selectors import (
    get_active_instagram_credential,
    get_instagram_credential,
)
from apps.integrations.instagram.client import InstagramAPIClient
from apps.integrations.meta.client import MetaAPIClient
from apps.integrations.meta.credentials import MetaCredentialService
from apps.integrations.meta.exceptions import MetaIntegrationError, MetaAPIError
from apps.social_accounts.models import SocialPlatform


CONTENT_PAGE_SIZE = 25
MAX_CONTENT_PAGES_PER_REQUEST = 2
CONTENT_CURSOR_MAX_AGE_SECONDS = 15 * 60
CONTENT_CURSOR_SALT = "insights.content-cursor.v1"
INSTAGRAM_INSIGHTS_PERMISSION = "instagram_business_manage_insights"
FACEBOOK_INSIGHTS_PERMISSION = "read_insights"
FACEBOOK_CONTENT_PERMISSION = "pages_read_engagement"
INSTAGRAM_IMPRESSIONS_UNSUPPORTED = "metric_deprecated"
FACEBOOK_REACH_UNSUPPORTED = "metric_not_supported_by_api_version"
FACEBOOK_IMPRESSIONS_UNSUPPORTED = "metric_not_supported_by_api_version"


def _metric(
    *, value=None, label, unit="count", availability="available",
    source, period=None, reason="", provider_metric="",
):
    if value is None and availability == "available":
        availability = "unavailable"
        reason = reason or "value_not_returned"
    return {
        "value": value,
        "label": label,
        "unit": unit,
        "availability": availability,
        "source": source,
        "provider_metric": provider_metric,
        "period": period,
        "reason": reason,
    }


def _unavailable_metric(
    *, label, source, availability, reason, unit="count", period=None,
    provider_metric="",
):
    return _metric(
        label=label,
        unit=unit,
        availability=availability,
        source=source,
        period=period,
        reason=reason,
        provider_metric=provider_metric,
    )


def _section(availability, reason="", metrics=None):
    return {
        "availability": availability,
        "reason": reason,
        "metrics": metrics or {},
    }


def _invalid_account_response(source, reason="invalid_account"):
    metric_specs = (
        (
            ("followers", "Followers", "followers_count"),
            ("reach", "Reach", "reach"),
            ("views", "Views", "views"),
            ("engagement", "Total interactions", "total_interactions"),
            ("accounts_engaged", "Accounts engaged", "accounts_engaged"),
            ("impressions", "Impressions", "impressions"),
        )
        if source == "instagram"
        else (
            ("followers", "Followers", "page_follows"),
            ("reach", "Reach", "page_impressions_unique"),
            ("impressions", "Impressions", "page_impressions"),
            ("engagement", "Post engagements", "page_post_engagements"),
            ("media_views", "Media views", "page_media_view"),
            ("unique_media_views", "Unique media views", "page_total_media_view_unique"),
        )
    )
    metrics = {
        key: _unavailable_metric(
            label=label,
            source=source,
            availability="not_supported" if (
                (source == "instagram" and key == "impressions")
                or (source == "facebook" and key in {"reach", "impressions"})
            ) else "unavailable",
            reason=(
                INSTAGRAM_IMPRESSIONS_UNSUPPORTED
                if source == "instagram" and key == "impressions"
                else FACEBOOK_REACH_UNSUPPORTED
                if source == "facebook" and key == "reach"
                else FACEBOOK_IMPRESSIONS_UNSUPPORTED
                if source == "facebook" and key == "impressions"
                else reason
            ),
            provider_metric=provider_metric,
        )
        for key, label, provider_metric in metric_specs
    }
    return {
        "provider_metadata": {
            "availability": "unavailable",
            "reason": reason,
            "provider_account_id": "",
            "account_name": "",
            "username": "",
            "profile_image": "",
            "media_count": None,
        },
        "metrics": metrics,
        "follower_growth": {
            "availability": "unavailable",
            "reason": reason,
            "current_value": metrics["followers"],
            "change": _unavailable_metric(
                label="Follower change",
                source=source,
                availability="unavailable",
                reason=reason,
            ),
            "points": [],
        },
        "account_performance": _section("unavailable", reason, metrics),
        "content_performance": {
            "availability": "unavailable",
            "reason": reason,
            "results": [],
            "next": None,
        },
    }


def _failure_status(error):
    """Map provider errors to safe, stable codes without returning raw payloads."""
    status_code = getattr(error, "status_code", None)
    payload = getattr(error, "error_payload", None)
    details = payload.get("error", payload) if isinstance(payload, dict) else {}
    if not isinstance(details, dict):
        details = {}
    code = details.get("code")
    try:
        code = int(code)
    except (TypeError, ValueError):
        code = None
    message = str(details.get("message") or "").lower()

    if any(phrase in message for phrase in ("not enough followers", "minimum number of followers")):
        return "unavailable", "insufficient_audience_size"
    if status_code == 401 or code == 190:
        return "unavailable", "invalid_credential"
    if status_code == 429 or code in {4, 17, 32, 613}:
        return "provider_error", "rate_limited"
    if code in {10, 200} or "permission" in message or "access denied" in message:
        return "permission_required", "permission_required"
    if code == 100 and any(word in message for word in ("metric", "unsupported", "not supported")):
        return "not_supported", "not_supported"
    if code == 100 and any(word in message for word in ("does not exist", "cannot be loaded", "invalid parameter")):
        return "unavailable", "provider_data_unavailable"
    return "provider_error", "provider_temporary_error"


def _provider_error_result(*, source, labels, error):
    availability, reason = _failure_status(error)
    return {
        label: _unavailable_metric(
            label=label.replace("_", " ").title(),
            source=source,
            availability=availability,
            reason=reason,
        )
        for label in labels
    }, availability, reason


def _resolve_instagram_token(account):
    credential = get_active_instagram_credential(social_account=account)
    if credential is None:
        # Use the existing selector to distinguish a missing credential from
        # one that exists but is inactive, revoked, expired, or out of date.
        get_instagram_credential(social_account=account)
        raise InstagramIntegrationError("Instagram credential is unavailable.")
    return decrypt_instagram_token(credential.encrypted_access_token)


def _resolve_facebook_token(account):
    return MetaCredentialService.get_access_token(social_account=account)


def _load_content_cursor(cursor, *, account, since, until):
    if not cursor:
        return None
    try:
        payload = signing.loads(
            cursor,
            salt=CONTENT_CURSOR_SALT,
            max_age=CONTENT_CURSOR_MAX_AGE_SECONDS,
        )
    except signing.BadSignature as exc:
        raise ValidationError({"cursor": "Invalid or expired content cursor."}) from exc
    expected = {
        "account_id": str(account.id),
        "organization_id": account.organization.organization_id,
        "since": since.isoformat() if since else None,
        "until": until.isoformat() if until else None,
        "platform": account.platform,
    }
    if not isinstance(payload, dict) or any(payload.get(key) != value for key, value in expected.items()):
        raise ValidationError({"cursor": "Content cursor does not match this account and date range."})
    return payload.get("after")


def _make_content_cursor(*, after, account, since, until):
    if not after:
        return None
    return signing.dumps(
        {
            "account_id": str(account.id),
            "organization_id": account.organization.organization_id,
            "platform": account.platform,
            "since": since.isoformat() if since else None,
            "until": until.isoformat() if until else None,
            "after": str(after),
        },
        salt=CONTENT_CURSOR_SALT,
        compress=True,
    )


def _media_is_in_range(item, *, since, until):
    timestamp = parse_datetime(str(item.get("timestamp") or item.get("created_time") or ""))
    if timestamp is None:
        return since is None and until is None
    item_date = timestamp.date()
    return (since is None or item_date >= since) and (until is None or item_date <= until)


def _insight_results(response):
    results = response.get("data", []) if isinstance(response, dict) else []
    return {
        item.get("name"): item
        for item in results
        if isinstance(item, dict) and item.get("name")
    } if isinstance(results, list) else {}


def _insight_total_value(result):
    total = result.get("total_value") if isinstance(result, dict) else None
    if isinstance(total, dict) and "value" in total:
        return total["value"], True
    if isinstance(total, (int, float)):
        return total, True
    return None, False


def _net_follows(value):
    if not isinstance(value, dict):
        return None
    normalized = {str(key).lower(): item for key, item in value.items()}
    follows = normalized.get("follows", normalized.get("follow"))
    unfollows = normalized.get("unfollows", normalized.get("unfollow"))
    if all(isinstance(item, (int, float)) for item in (follows, unfollows)):
        return follows - unfollows
    return None


def _insight_error_metrics(*, source, labels, error, permission):
    status, reason = _failure_status(error)
    if status == "permission_required":
        reason = permission
    return {
        name: _unavailable_metric(
            label=label,
            source=source,
            availability=status,
            reason=reason,
            provider_metric=provider_metric or name,
        )
        for name, label, provider_metric in labels
    }, status, reason


def _fetch_instagram_account_insights(*, client, account, token, since, until, current_followers):
    source = "instagram"
    metric_specs = (
        ("reach", "reach", "Reach"),
        ("views", "views", "Views"),
        ("engagement", "total_interactions", "Total interactions"),
        ("accounts_engaged", "accounts_engaged", "Accounts engaged"),
    )
    metrics = {
        name: _unavailable_metric(
            label=label,
            source=source,
            availability="unavailable",
            reason="metric_not_returned",
            provider_metric=provider_name,
        )
        for name, provider_name, label in metric_specs
    }
    metrics["followers"] = current_followers
    metrics["impressions"] = _unavailable_metric(
        label="Impressions",
        source=source,
        availability="not_supported",
        reason=INSTAGRAM_IMPRESSIONS_UNSUPPORTED,
        provider_metric="impressions",
    )
    growth = {
        "availability": "permission_required",
        "reason": INSTAGRAM_INSIGHTS_PERMISSION,
        "current_value": current_followers,
        "change": _unavailable_metric(
            label="Follower change",
            source=source,
            availability="permission_required",
            reason=INSTAGRAM_INSIGHTS_PERMISSION,
            provider_metric="follows_and_unfollows",
        ),
        "points": [],
    }
    insights_available = False
    params = {
        "metric": ",".join(provider_name for _, provider_name, _ in metric_specs),
        "period": "day",
        "metric_type": "total_value",
        "since": since.isoformat(),
        "until": until.isoformat(),
    }
    try:
        response = _instagram_graph_get(
            client,
            f"{account.platform_account_id}/insights",
            access_token=token,
            params=params,
        )
        insights_available = True
        results = _insight_results(response)
        for output_name, provider_name, label in metric_specs:
            value, returned = _insight_total_value(results.get(provider_name))
            metrics[output_name] = _metric(
                value=value,
                label=label,
                source=source,
                period="selected_range",
                availability="available" if returned else "unavailable",
                reason="" if returned else "metric_not_returned",
                provider_metric=provider_name,
            )
    except InstagramAPIError as exc:
        error_metrics, _, _ = _insight_error_metrics(
            source=source,
            labels=tuple(
                (name, label, provider_name)
                for name, provider_name, label in metric_specs
            ),
            error=exc,
            permission=INSTAGRAM_INSIGHTS_PERMISSION,
        )
        metrics.update(error_metrics)
        growth["availability"] = error_metrics["reach"]["availability"]
        growth["reason"] = error_metrics["reach"]["reason"]
        growth["change"] = _unavailable_metric(
            label="Follower change",
            source=source,
            availability=growth["availability"],
            reason=growth["reason"],
            provider_metric="follows_and_unfollows",
        )
        return metrics, growth, insights_available

    try:
        follow_response = _instagram_graph_get(
            client,
            f"{account.platform_account_id}/insights",
            access_token=token,
            params={
                "metric": "follows_and_unfollows",
                "period": "day",
                "metric_type": "total_value",
                "since": since.isoformat(),
                "until": until.isoformat(),
            },
        )
        follow_result = _insight_results(follow_response).get("follows_and_unfollows")
        raw_total, returned = _insight_total_value(follow_result)
        net_total = _net_follows(raw_total)
        values = follow_result.get("values", []) if isinstance(follow_result, dict) else []
        points = []
        for item in values if isinstance(values, list) else []:
            if not isinstance(item, dict) or not item.get("end_time"):
                continue
            net_value = _net_follows(item.get("value"))
            if net_value is not None:
                points.append({
                    "date": str(item["end_time"])[:10],
                    "value": _metric(
                        value=net_value,
                        label="Follower change",
                        source=source,
                        period="day",
                        provider_metric="follows_and_unfollows",
                    ),
                })
        growth_status = "available" if returned and net_total is not None else "unavailable"
        growth_reason = "" if growth_status == "available" else "metric_value_not_returned"
        growth = {
            "availability": growth_status,
            "reason": growth_reason,
            "current_value": current_followers,
            "change": _metric(
                value=net_total,
                label="Follower change",
                source=source,
                period="selected_range",
                availability=growth_status,
                reason=growth_reason,
                provider_metric="follows_and_unfollows",
            ),
            "points": points,
        }
    except InstagramAPIError as exc:
        status, reason = _failure_status(exc)
        if status == "permission_required":
            reason = INSTAGRAM_INSIGHTS_PERMISSION
        growth = {
            "availability": status,
            "reason": reason,
            "current_value": current_followers,
            "change": _unavailable_metric(
                label="Follower change",
                source=source,
                availability=status,
                reason=reason,
                provider_metric="follows_and_unfollows",
            ),
            "points": [],
        }
    return metrics, growth, insights_available


def _normalize_content_item(
    *, item, source, since, until, supports_insights, permission,
):
    content_id = str(item.get("id") or "")
    published_at = item.get("timestamp") or item.get("created_time")
    media_type = item.get("media_type") or item.get("type")
    caption = item.get("caption") if "caption" in item else item.get("message")
    permalink = item.get("permalink") or item.get("permalink_url")
    metrics = {}

    if "like_count" in item:
        metrics["likes"] = _metric(
            value=item["like_count"], label="Likes", source=source,
            period="lifetime",
        )
    else:
        metrics["likes"] = _unavailable_metric(
            label="Likes", source=source, availability="unavailable",
            reason="metric_not_returned",
        )

    if "comments_count" in item:
        metrics["comments"] = _metric(
            value=item["comments_count"], label="Comments", source=source,
            period="lifetime",
        )
    elif isinstance(item.get("comments"), dict) and isinstance(item["comments"].get("summary"), dict):
        metrics["comments"] = _metric(
            value=item["comments"]["summary"].get("total_count"),
            label="Comments", source=source, period="lifetime",
        )
    else:
        metrics["comments"] = _unavailable_metric(
            label="Comments", source=source, availability="unavailable",
            reason="metric_not_returned",
        )

    for key, label in (("reach", "Reach"), ("shares", "Shares"), ("saves", "Saves")):
        if key in item:
            value = item[key]
            if key == "shares" and isinstance(value, dict):
                value = value.get("count")
            metrics[key] = _metric(
                value=value, label=label, source=source, period="lifetime",
            )
        elif supports_insights:
            metrics[key] = _unavailable_metric(
                label=label, source=source, availability="unavailable",
                reason="metric_not_returned",
            )
        else:
            metrics[key] = _unavailable_metric(
                label=label, source=source, availability="permission_required",
                reason=permission,
            )

    return {
        "content_id": content_id,
        "media_type": str(media_type or ""),
        "caption": str(caption or ""),
        "permalink": str(permalink or ""),
        "published_at": published_at,
        "field_availability": {
            "content_id": "available" if content_id else "unavailable",
            "media_type": "available" if media_type else "unavailable",
            "caption": "available" if caption is not None else "unavailable",
            "permalink": "available" if permalink else "unavailable",
            "published_at": "available" if published_at else "unavailable",
        },
        "metrics": metrics,
    }


def _instagram_graph_get(client, path, *, access_token, params):
    try:
        return client.graph_get(path, access_token=access_token, params=params)
    except requests.RequestException:
        # The existing client places its token in request params. Do not let
        # a transport exception containing the request URL escape this layer.
        raise InstagramAPIError(
            "Instagram Graph request failed.",
            status_code=503,
        ) from None


def _fetch_instagram_content(
    *, client, account, token, since, until, after=None, insights_available=False,
):
    results = []
    next_after = None
    request_params = {
        "fields": "id,caption,media_type,permalink,timestamp,like_count,comments_count",
        "limit": CONTENT_PAGE_SIZE,
    }
    if after:
        request_params["after"] = after

    for _ in range(MAX_CONTENT_PAGES_PER_REQUEST):
        page = _instagram_graph_get(
            client,
            f"{account.platform_account_id}/media",
            access_token=token,
            params=dict(request_params),
        )
        items = page.get("data", [])
        if not isinstance(items, list):
            raise InstagramAPIError("Instagram returned an invalid media response.")
        for item in items:
            if (
                isinstance(item, dict)
                and item.get("id")
                and _media_is_in_range(item, since=since, until=until)
            ):
                normalized = _normalize_content_item(
                    item=item,
                    source="instagram",
                    since=since,
                    until=until,
                    supports_insights=insights_available,
                    permission=INSTAGRAM_INSIGHTS_PERMISSION,
                )
                normalized["metrics"]["impressions"] = _unavailable_metric(
                    label="Impressions",
                    source="instagram",
                    availability="not_supported",
                    reason=INSTAGRAM_IMPRESSIONS_UNSUPPORTED,
                )
                normalized["metrics"]["views"] = _unavailable_metric(
                    label="Views",
                    source="instagram",
                    availability=("unavailable" if insights_available else "permission_required"),
                    reason=("metric_not_returned" if insights_available else INSTAGRAM_INSIGHTS_PERMISSION),
                    provider_metric="views",
                )
                normalized["metrics"]["engagement"] = _unavailable_metric(
                    label="Engagement",
                    source="instagram",
                    availability=("unavailable" if insights_available else "permission_required"),
                    reason=("metric_not_returned" if insights_available else INSTAGRAM_INSIGHTS_PERMISSION),
                    provider_metric="total_interactions",
                )
                if insights_available and normalized["content_id"]:
                    try:
                        media_insights = _instagram_graph_get(
                            client,
                            f"{normalized['content_id']}/insights",
                            access_token=token,
                            params={"metric": "reach,views,shares,saved,total_interactions"},
                        )
                        insight_by_name = _insight_results(media_insights)
                        for output_name, provider_name, label in (
                            ("reach", "reach", "Reach"),
                            ("views", "views", "Views"),
                            ("shares", "shares", "Shares"),
                            ("saves", "saved", "Saves"),
                            ("engagement", "total_interactions", "Engagement"),
                        ):
                            value_result = insight_by_name.get(provider_name)
                            metric_value = None
                            returned = False
                            if value_result:
                                metric_values = value_result.get("values") or []
                                if metric_values and isinstance(metric_values[0], dict) and "value" in metric_values[0]:
                                    metric_value = metric_values[0]["value"]
                                    returned = True
                                else:
                                    metric_value, returned = _insight_total_value(value_result)
                            normalized["metrics"][output_name] = _metric(
                                value=metric_value,
                                label=label,
                                source="instagram",
                                period="lifetime",
                                availability="available" if returned else "unavailable",
                                reason="" if returned else "metric_not_returned",
                                provider_metric=provider_name,
                            )
                    except InstagramAPIError as exc:
                        error_metrics, _, _ = _insight_error_metrics(
                            source="instagram",
                            labels=(
                                ("reach", "Reach", "reach"),
                                ("views", "Views", "views"),
                                ("shares", "Shares", "shares"),
                                ("saves", "Saves", "saved"),
                                ("engagement", "Engagement", "total_interactions"),
                            ),
                            error=exc,
                            permission=INSTAGRAM_INSIGHTS_PERMISSION,
                        )
                        normalized["metrics"].update(error_metrics)
                results.append(normalized)
        paging = page.get("paging") if isinstance(page.get("paging"), dict) else {}
        cursors = paging.get("cursors") if isinstance(paging.get("cursors"), dict) else {}
        next_after = cursors.get("after") if paging.get("next") else None
        if not next_after:
            break
        request_params["after"] = next_after

    return {
        "availability": "available",
        "reason": "Date filtering is applied locally to the bounded provider page window.",
        "results": results,
        "next": _make_content_cursor(
            after=next_after,
            account=account,
            since=since,
            until=until,
        ),
    }


def _fetch_facebook_content(*, client, account, token, since, until, after=None):
    results = []
    next_after = None
    params = {
        "fields": (
            "id,message,created_time,permalink_url,shares,"
            "comments.limit(0).summary(true),reactions.limit(0).summary(true)"
        ),
        "limit": CONTENT_PAGE_SIZE,
    }
    if after:
        params["after"] = after

    for _ in range(MAX_CONTENT_PAGES_PER_REQUEST):
        page = client.get(
            f"/{account.platform_account_id}/posts",
            access_token=token,
            params=dict(params),
        )
        items = page.get("data", [])
        if not isinstance(items, list):
            raise MetaAPIError("Meta returned an invalid Page posts response.")
        for item in items:
            if (
                isinstance(item, dict)
                and item.get("id")
                and _media_is_in_range(item, since=since, until=until)
            ):
                normalized = _normalize_content_item(
                    item=item,
                    source="facebook",
                    since=since,
                    until=until,
                    supports_insights=True,
                    permission=FACEBOOK_INSIGHTS_PERMISSION,
                )
                reaction_summary = item.get("reactions", {}).get("summary", {})
                if isinstance(reaction_summary, dict) and "total_count" in reaction_summary:
                    normalized["metrics"]["reactions"] = _metric(
                        value=reaction_summary["total_count"],
                        label="Reactions",
                        source="facebook",
                        period="lifetime",
                    )
                else:
                    normalized["metrics"]["reactions"] = _unavailable_metric(
                        label="Reactions", source="facebook",
                        availability="unavailable", reason="metric_not_returned",
                    )
                results.append(normalized)
        paging = page.get("paging") if isinstance(page.get("paging"), dict) else {}
        cursors = paging.get("cursors") if isinstance(paging.get("cursors"), dict) else {}
        next_after = cursors.get("after") if paging.get("next") else None
        if not next_after:
            break
        params["after"] = next_after

    return {
        "availability": "available",
        "reason": "Date filtering is applied locally to the bounded provider page window.",
        "results": results,
        "next": _make_content_cursor(
            after=next_after,
            account=account,
            since=since,
            until=until,
        ),
    }


def _metric_values_from_insights(response, *, source, since=None, until=None):
    output = {}
    metric_labels = {
        "page_follows": ("Followers", "count"),
        "page_post_engagements": ("Post engagements", "count"),
        "page_media_view": ("Media views", "count"),
        "page_total_media_view_unique": ("Unique media views", "count"),
    }
    for result in response.get("data", []):
        if not isinstance(result, dict):
            continue
        name = result.get("name")
        if name not in metric_labels:
            continue
        label, unit = metric_labels[name]
        values = result.get("values") or []
        normalized_values = []
        for value in values:
            if not isinstance(value, dict) or not value.get("end_time"):
                continue
            point_date = parse_datetime(str(value["end_time"]))
            point_day = point_date.date() if point_date else None
            if point_day is None:
                continue
            if since and point_day < since:
                continue
            if until and point_day > until:
                continue
            normalized_values.append({
                "date": point_day.isoformat(),
                "value": _metric(
                    value=value.get("value"),
                    label=label,
                    unit=unit,
                    source=source,
                    period=result.get("period"),
                    provider_metric=name,
                ),
            })
        output[name] = [
            point for point in normalized_values
        ]
    return output


def _fetch_facebook(*, account, token, since, until, cursor_after=None):
    client = MetaAPIClient()
    source = "facebook"
    metrics = {}
    follower_growth = None
    metrics["reach"] = _unavailable_metric(
        label="Reach", source=source, availability="not_supported",
        reason=FACEBOOK_REACH_UNSUPPORTED, provider_metric="page_impressions_unique",
    )
    metrics["impressions"] = _unavailable_metric(
        label="Impressions", source=source, availability="not_supported",
        reason=FACEBOOK_IMPRESSIONS_UNSUPPORTED, provider_metric="page_impressions",
    )
    metrics["unique_media_views"] = _unavailable_metric(
        label="Unique media views", source=source, availability="unavailable",
        reason="metric_not_returned", provider_metric="page_total_media_view_unique",
    )
    provider_metadata = {
        "availability": "unavailable",
        "reason": "profile_not_returned",
        "provider_account_id": "",
        "account_name": "",
        "username": "",
        "profile_image": "",
        "media_count": None,
    }

    try:
        profile = client.get(
            f"/{account.platform_account_id}",
            access_token=token,
            params={"fields": "id,name,username,followers_count,picture"},
        )
        if str(profile.get("id")) != str(account.platform_account_id):
            return _invalid_account_response(source)
        picture = profile.get("picture") if isinstance(profile.get("picture"), dict) else {}
        picture_data = picture.get("data") if isinstance(picture.get("data"), dict) else {}
        provider_metadata = {
            "availability": "available",
            "reason": "",
            "provider_account_id": str(profile.get("id") or ""),
            "account_name": str(profile.get("name") or ""),
            "username": str(profile.get("username") or ""),
            "profile_image": str(picture_data.get("url") or ""),
            "media_count": None,
        }
        if "followers_count" in profile:
            metrics["followers"] = _metric(
                value=profile["followers_count"],
                label="Followers",
                source=source,
                period="current",
            )
    except MetaAPIError as exc:
        status, reason = _failure_status(exc)
        if reason == "invalid_credential":
            return _invalid_account_response(source, reason=reason)
        if status == "permission_required":
            reason = FACEBOOK_CONTENT_PERMISSION
        metrics["followers"] = _unavailable_metric(
            label="Followers", source=source, availability=status, reason=reason,
        )

    since_value = since.isoformat() if since else None
    until_value = until.isoformat() if until else None
    insights_params = {
        "metric": (
            "page_follows,page_post_engagements,page_media_view,"
            "page_total_media_view_unique"
        ),
        "period": "day",
    }
    if since_value:
        insights_params["since"] = since_value
    if until_value:
        insights_params["until"] = until_value

    try:
        insights = client.get(
            f"/{account.platform_account_id}/insights",
            access_token=token,
            params=insights_params,
        )
        normalized = _metric_values_from_insights(
            insights,
            source=source,
            since=since,
            until=until,
        )
        for api_name, output_name, label in (
            ("page_follows", "followers", "Followers"),
            ("page_post_engagements", "engagement", "Post engagements"),
            ("page_media_view", "media_views", "Media views"),
            ("page_total_media_view_unique", "unique_media_views", "Unique media views"),
        ):
            points = normalized.get(api_name)
            if points:
                latest = points[-1]["value"]
                metrics[output_name] = latest
                if api_name == "page_follows":
                    follower_growth = {
                        "availability": "available",
                        "reason": "",
                        "current_value": latest,
                        "change": _metric(
                            value=(points[-1]["value"]["value"] - points[0]["value"]["value"])
                            if len(points) > 1
                            and isinstance(points[-1]["value"]["value"], (int, float))
                            and isinstance(points[0]["value"]["value"], (int, float))
                            else None,
                            label="Follower change",
                            source=source,
                            period="selected_range",
                            availability="available" if len(points) > 1 else "unavailable",
                            reason="" if len(points) > 1 else "insufficient_historical_points",
                            provider_metric=api_name,
                        ),
                        "points": points,
                    }
            else:
                metrics.setdefault(
                    output_name,
                    _unavailable_metric(
                        label=label,
                        source=source,
                        availability="unavailable",
                        reason="metric_not_returned",
                        period="day",
                        provider_metric=api_name,
                    ),
                )
    except MetaAPIError as exc:
        status, reason = _failure_status(exc)
        if status == "permission_required":
            reason = FACEBOOK_INSIGHTS_PERMISSION
        for output_name, label, provider_metric in (
            ("followers", "Followers", "page_follows"),
            ("engagement", "Post engagements", "page_post_engagements"),
            ("media_views", "Media views", "page_media_view"),
            ("unique_media_views", "Unique media views", "page_total_media_view_unique"),
        ):
            metrics.setdefault(
                output_name,
                _unavailable_metric(
                    label=label,
                    source=source,
                    availability=status,
                    reason=reason,
                    period="day",
                    provider_metric=provider_metric,
                ),
            )
        follower_growth = {
            "availability": status,
            "reason": reason,
            "current_value": metrics["followers"],
            "change": _unavailable_metric(
                label="Follower change", source=source,
                availability=status, reason=reason, period="selected_range",
            ),
            "points": [],
        }

    try:
        content = _fetch_facebook_content(
            client=client,
            account=account,
            token=token,
            since=since,
            until=until,
            after=cursor_after,
        )
    except MetaAPIError as exc:
        content_status, content_reason = _failure_status(exc)
        if content_status == "permission_required":
            content_reason = FACEBOOK_CONTENT_PERMISSION
        content = {
            "availability": content_status,
            "reason": content_reason,
            "results": [],
            "next": None,
        }

    if follower_growth is None:
        current_followers = metrics.get("followers") or _unavailable_metric(
            label="Followers",
            source=source,
            availability="unavailable",
            reason="historical_data_unavailable",
            period="current",
        )
        follower_growth = {
            "availability": "unavailable",
            "reason": "historical_data_unavailable",
            "current_value": current_followers,
            "change": _unavailable_metric(
                label="Follower change",
                source=source,
                availability="unavailable",
                reason="historical_data_unavailable",
                period="selected_range",
            ),
            "points": [],
        }

    return {
        "provider_metadata": provider_metadata,
        "metrics": metrics,
        "follower_growth": follower_growth,
        "account_performance": _section(
            "available" if any(metric["availability"] == "available" for metric in metrics.values())
            else next(iter(metrics.values()))["availability"] if metrics
            else "unavailable",
            metrics=metrics,
        ),
        "content_performance": content,
    }


def fetch_provider_insights(*, account, since, until, cursor=None):
    """Fetch read-only provider data for one already-authorized SocialAccount."""
    cursor_after = _load_content_cursor(
        cursor,
        account=account,
        since=since,
        until=until,
    )
    if account.platform == SocialPlatform.INSTAGRAM:
        source = "instagram"
        account_metrics = {
            "followers": _unavailable_metric(
                label="Followers",
                source=source,
                availability="unavailable",
                reason="profile_not_returned",
                period="current",
            ),
            "reach": _unavailable_metric(
                label="Reach",
                source=source,
                availability="permission_required",
                reason=INSTAGRAM_INSIGHTS_PERMISSION,
                period="selected_range",
                provider_metric="reach",
            ),
            "views": _unavailable_metric(
                label="Views",
                source=source,
                availability="permission_required",
                reason=INSTAGRAM_INSIGHTS_PERMISSION,
                period="selected_range",
                provider_metric="views",
            ),
            "engagement": _unavailable_metric(
                label="Total interactions",
                source=source,
                availability="permission_required",
                reason=INSTAGRAM_INSIGHTS_PERMISSION,
                period="selected_range",
                provider_metric="total_interactions",
            ),
            "accounts_engaged": _unavailable_metric(
                label="Accounts engaged",
                source=source,
                availability="permission_required",
                reason=INSTAGRAM_INSIGHTS_PERMISSION,
                period="selected_range",
                provider_metric="accounts_engaged",
            ),
            "impressions": _unavailable_metric(
                label="Impressions",
                source=source,
                availability="not_supported",
                reason=INSTAGRAM_IMPRESSIONS_UNSUPPORTED,
                provider_metric="impressions",
            ),
        }
        follower_growth = {
            "availability": "permission_required",
            "reason": INSTAGRAM_INSIGHTS_PERMISSION,
            "current_value": account_metrics["followers"],
            "change": _unavailable_metric(
                label="Follower change",
                source=source,
                availability="permission_required",
                reason=INSTAGRAM_INSIGHTS_PERMISSION,
                period="selected_range",
                provider_metric="follows_and_unfollows",
            ),
            "points": [],
        }
        provider_metadata = {
            "availability": "unavailable",
            "reason": "profile_not_returned",
            "provider_account_id": "",
            "account_name": "",
            "username": "",
            "profile_image": "",
            "media_count": None,
        }
        try:
            token = _resolve_instagram_token(account)
            client = InstagramAPIClient()
            try:
                profile = _instagram_graph_get(
                    client,
                    account.platform_account_id,
                    access_token=token,
                    params={
                        "fields": "id,username,name,profile_picture_url,followers_count,media_count"
                    },
                )
                if str(profile.get("id")) != str(account.platform_account_id):
                    return _invalid_account_response(source)
                provider_metadata = {
                    "availability": "available",
                    "reason": "",
                    "provider_account_id": str(profile.get("id") or ""),
                    "account_name": str(profile.get("name") or ""),
                    "username": str(profile.get("username") or ""),
                    "profile_image": str(profile.get("profile_picture_url") or ""),
                    "media_count": profile.get("media_count"),
                }
                if "followers_count" in profile:
                    account_metrics["followers"] = _metric(
                        value=profile["followers_count"],
                        label="Followers",
                        source=source,
                        period="current",
                    )
                else:
                    account_metrics["followers"] = _unavailable_metric(
                        label="Followers",
                        source=source,
                        availability="unavailable",
                        reason="metric_not_returned",
                        period="current",
                    )
                follower_growth["current_value"] = account_metrics["followers"]
            except InstagramAPIError as exc:
                status, reason = _failure_status(exc)
                if reason == "invalid_credential":
                    return _invalid_account_response(source, reason=reason)
                account_metrics["followers"] = _unavailable_metric(
                    label="Followers",
                    source=source,
                    availability=status,
                    reason=reason,
                    period="current",
                )
                follower_growth["current_value"] = account_metrics["followers"]

            account_metrics, follower_growth, insights_available = _fetch_instagram_account_insights(
                client=client,
                account=account,
                token=token,
                since=since,
                until=until,
                current_followers=account_metrics["followers"],
            )

            content = _fetch_instagram_content(
                client=client,
                account=account,
                token=token,
                since=since,
                until=until,
                after=cursor_after,
                insights_available=insights_available,
            )
        except InstagramOAuthConfigurationError:
            config_metrics = {
                name: _unavailable_metric(
                    label=metric["label"],
                    source=source,
                    availability="provider_error",
                    reason="provider_configuration_error",
                    unit=metric["unit"],
                    period=metric["period"],
                )
                for name, metric in account_metrics.items()
                if metric["availability"] != "not_supported"
            }
            config_metrics.setdefault("impressions", account_metrics["impressions"])
            account_metrics = config_metrics
            follower_growth = {
                "availability": "provider_error",
                "reason": "provider_configuration_error",
                "current_value": account_metrics["followers"],
                "change": _unavailable_metric(
                    label="Follower change",
                    source=source,
                    availability="provider_error",
                    reason="provider_configuration_error",
                    period="selected_range",
                ),
                "points": [],
            }
            content = {
                "availability": "provider_error",
                "reason": "provider_configuration_error",
                "results": [],
                "next": None,
            }
        except (InstagramIntegrationError, InstagramAPIError) as exc:
            if isinstance(exc, InstagramAPIError):
                status, reason = _failure_status(exc)
            else:
                status, reason = "unavailable", "invalid_credential"
            content = {
                "availability": status,
                "reason": reason,
                "results": [],
                "next": None,
            }
            if status == "unavailable" and reason == "invalid_credential":
                account_metrics = {
                    name: _unavailable_metric(
                        label=metric["label"],
                        source=source,
                        availability=status,
                        reason=reason,
                        unit=metric["unit"],
                        period=metric["period"],
                    )
                    for name, metric in account_metrics.items()
                    if metric["availability"] != "not_supported"
                }
                account_metrics.setdefault("impressions", _unavailable_metric(
                    label="Impressions", source=source, availability="not_supported",
                    reason=INSTAGRAM_IMPRESSIONS_UNSUPPORTED, provider_metric="impressions",
                ))
                follower_growth = {
                    "availability": status,
                    "reason": reason,
                    "current_value": account_metrics["followers"],
                    "change": _unavailable_metric(
                        label="Follower change",
                        source=source,
                        availability=status,
                        reason=reason,
                        period="selected_range",
                    ),
                    "points": [],
                }
        return {
            "provider_metadata": provider_metadata,
            "metrics": account_metrics,
            "follower_growth": follower_growth,
            "account_performance": _section(
                "available"
                if any(metric["availability"] == "available" for metric in account_metrics.values())
                else content["availability"]
                if content["availability"] in {"unavailable", "provider_error"}
                else next(iter(account_metrics.values()))["availability"],
                ""
                if any(metric["availability"] == "available" for metric in account_metrics.values())
                else content["reason"]
                if content["availability"] in {"unavailable", "provider_error"}
                else next(iter(account_metrics.values()))["reason"],
                account_metrics,
            ),
            "content_performance": content,
        }

    if account.platform == SocialPlatform.FACEBOOK:
        try:
            token = _resolve_facebook_token(account)
        except MetaIntegrationError:
            source = "facebook"
            invalid_metrics = {
                name: _unavailable_metric(
                    label=label,
                    source=source,
                    availability="unavailable",
                    reason="invalid_credential",
                )
                for name, label in (
                    ("followers", "Followers"),
                    ("engagement", "Post engagements"),
                    ("media_views", "Media views"),
                )
            }
            unavailable = {
                "availability": "unavailable",
                "reason": "invalid_credential",
                "current_value": invalid_metrics["followers"],
                "change": _unavailable_metric(
                    label="Follower change", source=source,
                    availability="unavailable", reason="invalid_credential",
                ),
                "points": [],
            }
            return {
                "provider_metadata": {
                    "availability": "unavailable",
                    "reason": "invalid_credential",
                    "provider_account_id": "",
                    "account_name": "",
                    "username": "",
                    "profile_image": "",
                    "media_count": None,
                },
                "metrics": invalid_metrics,
                "follower_growth": unavailable,
                "account_performance": _section(
                    "unavailable", "invalid_credential", invalid_metrics,
                ),
                "content_performance": {
                    "availability": "unavailable",
                    "reason": "invalid_credential",
                    "results": [],
                    "next": None,
                },
            }
        return _fetch_facebook(
            account=account,
            token=token,
            since=since,
            until=until,
            cursor_after=cursor_after,
        )

    return {
        "provider_metadata": {
            "availability": "not_supported",
            "reason": "platform_not_supported",
            "provider_account_id": "",
            "account_name": "",
            "username": "",
            "profile_image": "",
            "media_count": None,
        },
        "metrics": {},
        "follower_growth": {
            "availability": "not_supported",
            "reason": "platform_not_supported",
            "current_value": _unavailable_metric(
                label="Followers", source=str(account.platform),
                availability="not_supported", reason="platform_not_supported",
            ),
            "change": _unavailable_metric(
                label="Follower change", source=str(account.platform),
                availability="not_supported", reason="platform_not_supported",
            ),
            "points": [],
        },
        "account_performance": _section("not_supported", "platform_not_supported"),
        "content_performance": {
            "availability": "not_supported",
            "reason": "platform_not_supported",
            "results": [],
            "next": None,
        },
    }
