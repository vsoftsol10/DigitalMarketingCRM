import logging
import re
import uuid
from datetime import datetime, timedelta, timezone as datetime_timezone
from typing import Dict, Optional

import redis
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountStatus,
    SocialConnection,
    SocialConnectionProvider,
    SocialConnectionStatus,
)

from .client import MetaAPIClient
from .crypto import decrypt_token, encrypt_token
from .exceptions import MetaAPIError
from .models import (
    MetaAccountCredential,
    MetaCredentialStatus,
    MetaCredentialType,
    MetaProviderExpiryState,
    MetaTokenMaintenanceRun,
)
from .selectors import get_meta_connection_credential

logger = logging.getLogger(__name__)

META_USER_DATA_ACCESS_WARNING_WINDOW = timedelta(days=14)
META_USER_DATA_ACCESS_URGENT_WINDOW = timedelta(days=3)
META_USER_DATA_ACCESS_EXPIRY_EVENT_PREFIX = "meta-user-data-access-expiry"

_RELEASE_LOCK_SCRIPT = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""


class MetaTokenLifecycleService:
    """
    Production-grade lifecycle management for Facebook Page
    access tokens.

    Facebook Page tokens are handled differently from Instagram
    long-lived user tokens.

    Lifecycle strategy:

        1. Validate the currently stored Page token.
        2. If valid:
               keep ACTIVE
               update last_verified_at
               mark SocialAccount connected/valid
        3. If invalid:
               use the parent Meta USER token
               request a fresh Page token
        4. Validate the newly received Page token.
        5. Save the new token atomically.
        6. If recovery fails because authorization is lost:
               mark Page credential INVALID
               mark SocialAccount ERROR
        7. Temporary provider/network errors:
               do not invalidate the account
               retry on the next scheduled cycle.
        8. Manually REVOKED credentials are never restored
           automatically.
    """

    LOCK_TIMEOUT_SECONDS = getattr(
        settings,
        "META_TOKEN_LIFECYCLE_LOCK_TIMEOUT_SECONDS",
        5 * 60,
    )

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
        *,
        api_client: Optional[MetaAPIClient] = None,
    ):
        self.api = api_client or MetaAPIClient()
        self._user_renewal_redis_client = None

    @staticmethod
    def _safe_parent_permissions(response, *, sensitive_values=()):
        """Keep only permission names and normalized provider statuses."""
        if not isinstance(response, dict) or not isinstance(response.get("data"), list):
            return None
        safe = []
        for item in response["data"]:
            if not isinstance(item, dict):
                continue
            name = item.get("permission")
            if not isinstance(name, str) or not re.fullmatch(
                r"[a-z][a-z0-9_]{0,99}",
                name,
            ):
                continue
            if name in sensitive_values:
                continue
            status = item.get("status")
            if (
                not isinstance(status, str)
                or status.lower() not in {"granted", "declined", "expired"}
            ):
                status = "unknown"
            safe.append({"permission": name, "status": status.lower()})
        return safe

    @staticmethod
    def _provider_timestamp(value):
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value if value >= 0 else None
        if isinstance(value, str) and value.strip().isdigit():
            try:
                return int(value.strip())
            except ValueError:
                return None
        return None

    @staticmethod
    def _provider_datetime(timestamp):
        if not isinstance(timestamp, int) or isinstance(timestamp, bool) or timestamp <= 0:
            return None
        try:
            return datetime.fromtimestamp(timestamp, tz=datetime_timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None

    @classmethod
    def _parent_expiry_health_metadata(cls, credential, debug):
        """Return safe USER expiry updates without erasing known metadata."""
        updates = {}
        raw_expires_at = debug.get("expires_at")
        expires_at = cls._provider_timestamp(raw_expires_at)
        if expires_at == 0:
            expiry_state = MetaProviderExpiryState.NO_FINITE_EXPIRY
            provider_expiry = None
            updates.update(
                provider_expiry_state=expiry_state,
                provider_expires_at=None,
            )
        elif expires_at is not None:
            provider_expiry = cls._provider_datetime(expires_at)
            if provider_expiry is not None:
                expiry_state = MetaProviderExpiryState.FINITE
                updates.update(
                    provider_expiry_state=expiry_state,
                    provider_expires_at=provider_expiry,
                )
            else:
                expires_at = None

        if expires_at is None:
            previous_state = credential.provider_expiry_state
            if previous_state not in {
                MetaProviderExpiryState.FINITE,
                MetaProviderExpiryState.NO_FINITE_EXPIRY,
            }:
                expiry_state = MetaProviderExpiryState.UNKNOWN
                updates["provider_expiry_state"] = expiry_state
            else:
                expiry_state = previous_state
            # Missing or invalid provider metadata does not overwrite a
            # previously stored provider expiry.
            provider_expiry = credential.provider_expires_at

        raw_data_access_expires_at = debug.get("data_access_expires_at")
        data_access_timestamp = cls._provider_timestamp(raw_data_access_expires_at)
        data_access_expiry = cls._provider_datetime(data_access_timestamp)
        if data_access_expiry is not None:
            updates["data_access_expires_at"] = data_access_expiry
        else:
            # Keep prior known data-access metadata when a diagnostic omits
            # or malforms this independent expiry field.
            data_access_expiry = credential.data_access_expires_at

        return updates, expiry_state, provider_expiry, data_access_expiry

    @staticmethod
    def _parent_error_is_definitive(error):
        details = MetaAPIClient.safe_error_metadata(error)
        return (
            details["http_status"] in {401, 403}
            or details["graph_error_code"] in {10, 190, 200}
        )

    @staticmethod
    def _save_parent_health_if_current(
        credential,
        *,
        expected_access_token,
        expected_updated_at,
        expected_last_verified_at,
        **updates,
    ):
        """Save health data only if this is still the credential checked."""
        with transaction.atomic():
            current = (
                MetaAccountCredential.objects.select_for_update()
                .filter(
                    pk=credential.pk,
                    credential_type=MetaCredentialType.USER,
                    is_deleted=False,
                )
                .first()
            )
            if (
                current is None
                or current.access_token != expected_access_token
                or current.updated_at != expected_updated_at
                or current.last_verified_at != expected_last_verified_at
            ):
                return None

            for field, value in updates.items():
                setattr(current, field, value)
            current.save(update_fields=[*updates, "updated_at"])
            return current.updated_at

    @staticmethod
    def _record_parent_reconnect_required(credential):
        connection = credential.social_connection
        if connection is None:
            return
        from apps.notifications.services import (
            record_social_credential_reconnect_required,
        )

        record_social_credential_reconnect_required(
            organization=connection.organization,
            scope="meta-connection",
            subject_id=connection.pk,
            platform="facebook",
        )

    @staticmethod
    def _resolve_parent_reconnect_required(credential):
        connection = credential.social_connection
        if connection is None:
            return
        from apps.notifications.services import (
            resolve_social_credential_reconnect_required,
        )

        resolve_social_credential_reconnect_required(
            organization=connection.organization,
            scope="meta-connection",
            subject_id=connection.pk,
        )

    @staticmethod
    def _record_page_reconnect_required(credential):
        account = credential.social_account
        if account is None:
            return
        from apps.notifications.services import (
            record_social_credential_reconnect_required,
        )

        record_social_credential_reconnect_required(
            organization=account.organization,
            scope="facebook-page",
            subject_id=account.pk,
            platform="facebook",
            account_name=account.account_name or account.username,
        )

    @staticmethod
    def _resolve_page_reconnect_required(credential):
        account = credential.social_account
        if account is None:
            return
        from apps.notifications.services import (
            resolve_social_credential_reconnect_required,
        )

        resolve_social_credential_reconnect_required(
            organization=account.organization,
            scope="facebook-page",
            subject_id=account.pk,
        )

    def _check_parent_user_credential(self, credential):
        """Health-check one USER credential without changing its token/expiry."""
        expected_access_token = credential.access_token
        expected_updated_at = credential.updated_at
        expected_last_verified_at = credential.last_verified_at
        health_updated_at = expected_updated_at
        try:
            user_token = decrypt_token(expected_access_token)
            if not user_token:
                raise MetaAPIError("Meta USER credential is empty.")
            debug = self.api.diagnose_token(access_token=user_token)
            if not isinstance(debug, dict) or not isinstance(debug.get("is_valid"), bool):
                logger.warning(
                    "Meta parent credential diagnostic was incomplete. credential_id=%s",
                    credential.id,
                )
                return "retry"

            allowed_types = {"USER", "PAGE", "APP", "CLIENT_APP", "SYSTEM_USER"}
            raw_token_type = debug.get("type")
            token_type = (
                raw_token_type.upper()
                if isinstance(raw_token_type, str)
                and raw_token_type.upper() in allowed_types
                else "unknown"
            )
            if token_type == "unknown":
                logger.warning(
                    "Meta parent credential diagnostic was incomplete. credential_id=%s",
                    credential.id,
                )
                return "retry"
            (
                expiry_metadata_updates,
                _expiry_state,
                expires_at,
                data_expires_at,
            ) = self._parent_expiry_health_metadata(credential, debug)
            checked_at = timezone.now()

            if not debug["is_valid"]:
                health_updated_at = self._save_parent_health_if_current(
                    credential,
                    expected_access_token=expected_access_token,
                    expected_updated_at=expected_updated_at,
                    expected_last_verified_at=expected_last_verified_at,
                    provider_token_type=token_type,
                    provider_is_valid=debug["is_valid"],
                    **expiry_metadata_updates,
                    last_health_check_at=checked_at,
                    status=MetaCredentialStatus.INVALID,
                )
                if health_updated_at is None:
                    return "retry"
                self._record_parent_reconnect_required(credential)
                logger.warning(
                    "Meta parent token is invalid and requires reconnect. credential_id=%s",
                    credential.id,
                )
                return "reconnect_needed"

            health_updated_at = self._save_parent_health_if_current(
                credential,
                expected_access_token=expected_access_token,
                expected_updated_at=expected_updated_at,
                expected_last_verified_at=expected_last_verified_at,
                provider_token_type=token_type,
                provider_is_valid=debug["is_valid"],
                **expiry_metadata_updates,
            )
            if health_updated_at is None:
                return "retry"

            permissions_response = self.api.get_user_permissions(access_token=user_token)
            permissions = self._safe_parent_permissions(
                permissions_response,
                sensitive_values={
                    user_token,
                    getattr(settings, "META_APP_SECRET", ""),
                },
            )
            if permissions is None:
                logger.warning(
                    "Meta parent permissions diagnostic was incomplete. credential_id=%s",
                    credential.id,
                )
                return "retry"

            prior_grants = {
                entry.get("permission")
                for entry in credential.granted_permissions
                if isinstance(entry, dict) and entry.get("status") == "granted"
            }
            current_grants = {
                entry["permission"]
                for entry in permissions
                if entry["status"] == "granted"
            }
            required_permission_missing = "pages_show_list" not in current_grants
            permission_lost = (
                "pages_show_list" in prior_grants
                and "pages_show_list" not in current_grants
            )
            expired = bool(
                (expires_at and expires_at <= checked_at)
                or (data_expires_at and data_expires_at <= checked_at)
            )
            if token_type not in {"USER", "SYSTEM_USER"}:
                health_status = MetaCredentialStatus.ERROR
                outcome = "reconnect_needed"
            elif expired:
                health_status = MetaCredentialStatus.EXPIRED
                outcome = "reconnect_needed"
            elif required_permission_missing or permission_lost:
                health_status = MetaCredentialStatus.ERROR
                outcome = "reconnect_needed"
            else:
                health_status = MetaCredentialStatus.ACTIVE
                outcome = "valid"

            health_updated_at = self._save_parent_health_if_current(
                credential,
                expected_access_token=expected_access_token,
                expected_updated_at=health_updated_at,
                expected_last_verified_at=expected_last_verified_at,
                granted_permissions=permissions,
                last_health_check_at=checked_at,
                status=health_status,
            )
            if health_updated_at is None:
                return "retry"
            if outcome == "reconnect_needed":
                self._record_parent_reconnect_required(credential)
            else:
                self._resolve_parent_reconnect_required(credential)
            logger.info(
                "Meta parent credential health checked. credential_id=%s outcome=%s token_type=%s permission_count=%s",
                credential.id,
                outcome,
                token_type,
                len(permissions),
            )
            return outcome
        except MetaAPIError as exc:
            details = self.api.safe_error_metadata(exc)
            if self._is_temporary_error(exc) or not self._parent_error_is_definitive(exc):
                logger.warning(
                    "Meta parent credential health check will retry. credential_id=%s http_status=%s graph_error_code=%s graph_error_subcode=%s",
                    credential.id,
                    details["http_status"],
                    details["graph_error_code"],
                    details["graph_error_subcode"],
                )
                return "retry"
            health_status = (
                MetaCredentialStatus.INVALID
                if details["graph_error_code"] == 190
                else MetaCredentialStatus.ERROR
            )
            health_updated_at = self._save_parent_health_if_current(
                credential,
                expected_access_token=expected_access_token,
                expected_updated_at=health_updated_at,
                expected_last_verified_at=expected_last_verified_at,
                status=health_status,
            )
            if health_updated_at is None:
                return "retry"
            self._record_parent_reconnect_required(credential)
            logger.warning(
                "Meta parent credential requires reconnect. credential_id=%s http_status=%s graph_error_code=%s graph_error_subcode=%s",
                credential.id,
                details["http_status"],
                details["graph_error_code"],
                details["graph_error_subcode"],
            )
            return "reconnect_needed"
        except Exception:
            logger.warning(
                "Meta parent credential health check failed safely. credential_id=%s",
                credential.id,
            )
            return "retry"

    def check_user_credential_health_after_oauth(self, credential_id):
        """Persist fresh provider metadata for a just-saved USER credential."""
        try:
            credential = MetaAccountCredential.objects.filter(
                pk=credential_id,
                credential_type=MetaCredentialType.USER,
                status=MetaCredentialStatus.ACTIVE,
                is_deleted=False,
            ).first()
            if credential is None:
                return "skipped"
            return self._check_parent_user_credential(credential)
        except Exception:
            logger.warning(
                "Meta OAuth credential health check deferred safely. credential_id=%s",
                credential_id,
            )
            return "retry"

    def validate_and_persist_user_credential_health(
        self,
        credential_id,
        *,
        required_permissions,
    ):
        """Validate one active USER credential, then persist health metadata only.

        This deliberately does not use the broader scheduled health-check path,
        which can change credential status and reconnect notifications.
        """
        try:
            credential = MetaAccountCredential.objects.get(
                pk=credential_id,
                credential_type=MetaCredentialType.USER,
                status=MetaCredentialStatus.ACTIVE,
                is_deleted=False,
            )
        except MetaAccountCredential.DoesNotExist:
            return "skipped"

        if isinstance(required_permissions, str):
            raise MetaAPIError("Meta USER credential validation failed.")
        try:
            required = list(required_permissions)
        except TypeError:
            raise MetaAPIError("Meta USER credential validation failed.") from None
        if not required or any(
            not isinstance(permission, str)
            or not re.fullmatch(r"[a-z][a-z0-9_]{0,99}", permission)
            for permission in required
        ):
            raise MetaAPIError("Meta USER credential validation failed.")
        required = set(required)

        expected_access_token = credential.access_token
        expected_updated_at = credential.updated_at
        try:
            user_token = decrypt_token(expected_access_token)
            if not user_token:
                raise ValueError("empty credential")

            configured_app_id = str(
                getattr(settings, "META_APP_ID", "") or ""
            ).strip()
            if not configured_app_id:
                raise ValueError("app id unavailable")

            debug = self.api.diagnose_token(access_token=user_token)
            if not isinstance(debug, dict):
                raise ValueError("invalid diagnostic response")
            if str(debug.get("app_id") or "") != configured_app_id:
                raise ValueError("app mismatch")
            token_type = debug.get("type")
            if not isinstance(token_type, str) or token_type.upper() != "USER":
                raise ValueError("unexpected token type")
            if debug.get("is_valid") is not True:
                raise ValueError("invalid token")

            now = timezone.now()
            provider_expiry_timestamp = self._provider_timestamp(
                debug.get("expires_at")
            )
            if provider_expiry_timestamp == 0:
                provider_expiry_state = MetaProviderExpiryState.NO_FINITE_EXPIRY
                provider_expires_at = None
            elif (
                provider_expiry_timestamp is not None
                and provider_expiry_timestamp > int(now.timestamp())
            ):
                provider_expiry_state = MetaProviderExpiryState.FINITE
                provider_expires_at = self._provider_datetime(
                    provider_expiry_timestamp
                )
                if provider_expires_at is None:
                    raise ValueError("invalid provider expiry")
            else:
                raise ValueError("invalid or expired provider expiry")

            data_access_timestamp = self._provider_timestamp(
                debug.get("data_access_expires_at")
            )
            if (
                data_access_timestamp is None
                or data_access_timestamp <= int(now.timestamp())
            ):
                raise ValueError("invalid or expired data-access expiry")
            data_access_expires_at = self._provider_datetime(data_access_timestamp)
            if data_access_expires_at is None:
                raise ValueError("invalid data-access expiry")

            permissions_response = self.api.get_user_permissions(
                access_token=user_token,
            )
            permissions = self._safe_parent_permissions(
                permissions_response,
                sensitive_values={
                    user_token,
                    getattr(settings, "META_APP_SECRET", ""),
                },
            )
            if permissions is None:
                raise ValueError("invalid permissions response")
            granted = {
                item["permission"]
                for item in permissions
                if item["status"] == "granted"
            }
            if not required.issubset(granted):
                raise ValueError("required permissions missing")
        except Exception:
            # Keep provider errors and any diagnostic payload out of exceptions
            # exposed by this narrowly scoped operation.
            raise MetaAPIError("Meta USER credential validation failed.") from None

        updates = {
            "provider_token_type": "USER",
            "provider_is_valid": True,
            "provider_expiry_state": provider_expiry_state,
            "provider_expires_at": provider_expires_at,
            "data_access_expires_at": data_access_expires_at,
            "last_health_check_at": now,
        }
        with transaction.atomic():
            current = (
                MetaAccountCredential.objects.select_for_update()
                .filter(
                    pk=credential_id,
                    credential_type=MetaCredentialType.USER,
                    status=MetaCredentialStatus.ACTIVE,
                    is_deleted=False,
                )
                .first()
            )
            if (
                current is None
                or current.access_token != expected_access_token
                or current.updated_at != expected_updated_at
            ):
                return "stale"

            updated_count = MetaAccountCredential.objects.filter(
                pk=credential_id,
                credential_type=MetaCredentialType.USER,
                status=MetaCredentialStatus.ACTIVE,
                is_deleted=False,
                access_token=expected_access_token,
                updated_at=expected_updated_at,
            ).update(**updates)
            if updated_count != 1:
                return "stale"
        return "updated"

    @staticmethod
    def _user_credential_is_due_for_renewal(
        credential,
        *,
        now,
        window,
        cooldown=None,
    ):
        if (
            credential.credential_type != MetaCredentialType.USER
            or credential.status != MetaCredentialStatus.ACTIVE
            or credential.is_deleted
            or credential.provider_token_type != "USER"
            or credential.provider_expiry_state != MetaProviderExpiryState.FINITE
            or credential.provider_is_valid is not True
        ):
            return False

        if cooldown is None:
            cooldown = timedelta(
                seconds=settings.META_USER_TOKEN_RENEWAL_COOLDOWN_SECONDS
            )
        last_renewed_at = credential.last_user_token_renewed_at
        if last_renewed_at is not None and last_renewed_at > now - cooldown:
            return False

        provider_expiry = credential.provider_expires_at
        data_access_expiry = credential.data_access_expires_at
        if (
            provider_expiry is None
            or provider_expiry <= now
            or provider_expiry > now + window
            or data_access_expiry is None
            or data_access_expiry <= now
        ):
            return False

        return True

    @staticmethod
    def _user_credential_is_safe_for_confirmed_no_finite_replacement(
        credential,
        *,
        now,
        cooldown,
    ):
        """Check the narrow source-credential rules for a manual test call."""
        last_renewed_at = credential.last_user_token_renewed_at
        return bool(
            credential.credential_type == MetaCredentialType.USER
            and credential.status == MetaCredentialStatus.ACTIVE
            and not credential.is_deleted
            and credential.provider_token_type == "USER"
            and credential.provider_is_valid is True
            and credential.provider_expiry_state
            == MetaProviderExpiryState.NO_FINITE_EXPIRY
            and credential.provider_expires_at is None
            and credential.data_access_expires_at is not None
            and credential.data_access_expires_at > now
            and (
                last_renewed_at is None
                or last_renewed_at <= now - cooldown
            )
        )

    def _replace_no_finite_user_credential_for_controlled_test(
        self,
        credential_id,
        *,
        expected_organization_id,
        expected_provider_user_id,
        confirm_external_exchange=False,
    ):
        """Run one explicitly confirmed, isolated USER replacement operation.

        This internal path is not wired to HTTP, OAuth, Celery, or automatic
        renewal. It only permits a currently confirmed NO_FINITE_EXPIRY USER
        credential and delegates exchange, validation, locking, and
        persistence to the same implementation used by automatic renewal.
        """
        if confirm_external_exchange is not True:
            raise ValueError("Explicit external exchange confirmation is required.")
        if not credential_id:
            raise ValueError("An explicit credential ID is required.")
        expected_provider_user_id = str(expected_provider_user_id or "").strip()
        if not expected_provider_user_id:
            raise ValueError("An explicit Meta provider user ID is required.")
        expected_organization_id = str(expected_organization_id or "").strip()
        if not expected_organization_id:
            raise ValueError("An explicit organization ID is required.")

        return self._renew_user_credential(
            credential_id,
            required_permissions=settings.META_USER_TOKEN_RENEWAL_REQUIRED_PERMISSIONS,
            allow_confirmed_no_finite_source=True,
            expected_organization_id=expected_organization_id,
            expected_provider_user_id=expected_provider_user_id,
            confirm_external_exchange=True,
        )

    @staticmethod
    def _user_renewal_lock_timeout_seconds():
        task_limit = getattr(settings, "CELERY_TASK_TIME_LIMIT", None)
        if (
            not isinstance(task_limit, int)
            or isinstance(task_limit, bool)
            or task_limit < 1
        ):
            raise RuntimeError("Celery hard task limit is unavailable.")
        safety_interval = MetaTokenLifecycleService.LOCK_TIMEOUT_SECONDS
        if (
            not isinstance(safety_interval, int)
            or isinstance(safety_interval, bool)
            or safety_interval < 1
        ):
            raise RuntimeError("Meta lock safety interval is invalid.")
        return task_limit + safety_interval

    def _get_user_renewal_redis_client(self):
        if self._user_renewal_redis_client is not None:
            return self._user_renewal_redis_client

        cache_config = settings.CACHES.get("default", {})
        if cache_config.get("BACKEND") != "django.core.cache.backends.redis.RedisCache":
            raise RuntimeError("Configured default cache is not RedisCache.")
        location = cache_config.get("LOCATION")
        if isinstance(location, (list, tuple)):
            if len(location) != 1:
                raise RuntimeError("USER renewal lock requires one Redis endpoint.")
            location = location[0]
        if not isinstance(location, str) or not location.strip():
            raise RuntimeError("Configured Redis endpoint is unavailable.")

        cache_options = cache_config.get("OPTIONS", {})
        redis_options = {}
        if "db" in cache_options:
            redis_options["db"] = cache_options["db"]
        client = redis.Redis.from_url(location, **redis_options)
        self._user_renewal_redis_client = client
        return client

    def _acquire_user_renewal_lock(self, credential_id):
        lock_key = cache.make_key(f"meta:user-token-renewal:{credential_id}")
        lock_token = f"{credential_id}:{uuid.uuid4()}"
        redis_client = self._get_user_renewal_redis_client()
        if not redis_client.set(
            lock_key,
            lock_token,
            nx=True,
            ex=self._user_renewal_lock_timeout_seconds(),
        ):
            return None
        return lock_token

    def _release_user_renewal_lock(self, credential_id, lock_token):
        lock_key = cache.make_key(f"meta:user-token-renewal:{credential_id}")
        try:
            redis_client = self._get_user_renewal_redis_client()
            redis_client.eval(
                _RELEASE_LOCK_SCRIPT,
                1,
                lock_key,
                lock_token,
            )
        except Exception:
            logger.error(
                "Failed to release Meta USER renewal lock. credential_id=%s",
                credential_id,
            )

    def renew_due_user_credentials(self):
        """Renew due Facebook USER tokens without changing PAGE lifecycle flow."""
        now = timezone.now()
        renewal_window = timedelta(
            seconds=settings.META_USER_TOKEN_RENEWAL_WINDOW_SECONDS
        )
        renewal_cooldown = timedelta(
            seconds=settings.META_USER_TOKEN_RENEWAL_COOLDOWN_SECONDS
        )
        cutoff = now + renewal_window
        required_permissions = settings.META_USER_TOKEN_RENEWAL_REQUIRED_PERMISSIONS

        candidate_ids = (
            MetaAccountCredential.objects.filter(
                credential_type=MetaCredentialType.USER,
                status=MetaCredentialStatus.ACTIVE,
                is_deleted=False,
                social_connection__isnull=False,
                social_connection__is_deleted=False,
                social_connection__provider=SocialConnectionProvider.META,
                social_connection__status=SocialConnectionStatus.ACTIVE,
                provider_expiry_state=MetaProviderExpiryState.FINITE,
                provider_is_valid=True,
                provider_token_type="USER",
                provider_expires_at__gt=now,
                provider_expires_at__lte=cutoff,
                data_access_expires_at__gt=now,
            )
            .filter(
                Q(last_user_token_renewed_at__isnull=True)
                | Q(last_user_token_renewed_at__lte=now - renewal_cooldown)
            )
            .order_by("id")
            .values_list("id", flat=True)
        )
        result = {
            "eligible": 0,
            "renewed": 0,
            "skipped": 0,
            "locked": 0,
            "stale": 0,
            "retry": 0,
        }
        for credential_id in candidate_ids.iterator(chunk_size=200):
            result["eligible"] += 1
            outcome = self._renew_user_credential(
                credential_id,
                required_permissions=required_permissions,
            )
            result[outcome] += 1
        logger.info("Meta USER token renewal pass completed: %s", result)
        return result

    def _renew_user_credential(
        self,
        credential_id,
        *,
        required_permissions,
        allow_confirmed_no_finite_source=False,
        expected_organization_id=None,
        expected_provider_user_id=None,
        confirm_external_exchange=False,
    ):
        if allow_confirmed_no_finite_source and (
            confirm_external_exchange is not True
            or not expected_organization_id
            or not expected_provider_user_id
        ):
            return "skipped"
        try:
            lock_token = self._acquire_user_renewal_lock(str(credential_id))
        except Exception as exc:
            logger.warning(
                "Meta USER token renewal lock unavailable. credential_id=%s error_type=%s",
                credential_id,
                type(exc).__name__,
            )
            return "retry"
        if lock_token is None:
            return "locked"

        original_token = None
        returned_token = None
        encrypted_returned_token = None
        persistence_ready = False
        try:
            credential = MetaAccountCredential.objects.get(
                pk=credential_id,
                credential_type=MetaCredentialType.USER,
                status=MetaCredentialStatus.ACTIVE,
                is_deleted=False,
                social_connection__provider=SocialConnectionProvider.META,
                social_connection__is_deleted=False,
                social_connection__status=SocialConnectionStatus.ACTIVE,
                provider_token_type="USER",
            )
            stored_provider_user_id = str(
                getattr(
                    getattr(credential, "social_connection", None),
                    "provider_user_id",
                    "",
                )
                or ""
            ).strip()
            stored_organization_id = str(
                getattr(
                    getattr(
                        getattr(credential, "social_connection", None),
                        "organization",
                        None,
                    ),
                    "organization_id",
                    "",
                )
                or ""
            ).strip()
            if (
                not stored_provider_user_id
                or (
                    expected_organization_id is not None
                    and stored_organization_id != expected_organization_id
                )
                or (
                    expected_provider_user_id is not None
                    and stored_provider_user_id != expected_provider_user_id
                )
            ):
                return "skipped"
            expected_user_id = stored_provider_user_id

            now = timezone.now()
            renewal_cooldown = timedelta(
                seconds=settings.META_USER_TOKEN_RENEWAL_COOLDOWN_SECONDS
            )
            if allow_confirmed_no_finite_source:
                eligible = self._user_credential_is_safe_for_confirmed_no_finite_replacement(
                    credential,
                    now=now,
                    cooldown=renewal_cooldown,
                )
            else:
                renewal_window = timedelta(
                    seconds=settings.META_USER_TOKEN_RENEWAL_WINDOW_SECONDS
                )
                eligible = self._user_credential_is_due_for_renewal(
                    credential,
                    now=now,
                    window=renewal_window,
                    cooldown=renewal_cooldown,
                )
            if not eligible:
                return "skipped"

            if (
                expected_provider_user_id is not None
                and expected_user_id != expected_provider_user_id
            ):
                return "skipped"

            expected_access_token = credential.access_token
            expected_updated_at = credential.updated_at
            expected_user_id = str(
                getattr(
                    getattr(credential, "social_connection", None),
                    "provider_user_id",
                    "",
                )
                or ""
            ).strip()
            if not expected_user_id:
                raise MetaAPIError("Meta USER identity is unavailable for renewal.")
            original_token = decrypt_token(expected_access_token)
            exchange_started_at = timezone.now()
            exchange_result = self.api.exchange_user_access_token(
                access_token=original_token,
                required_permissions=required_permissions,
                expected_user_id=expected_user_id,
            )
            if not isinstance(exchange_result, dict):
                raise MetaAPIError("Meta USER token renewal validation failed.")

            returned_token = exchange_result.get("access_token")
            if not isinstance(returned_token, str) or not returned_token.strip():
                raise MetaAPIError("Meta USER token renewal validation failed.")
            returned_token = returned_token.strip()

            provider_expiry_state = exchange_result.get("provider_expiry_state")
            provider_expires_at = exchange_result.get("provider_expires_at")
            data_access_expires_at = exchange_result.get("data_access_expires_at")
            validated_at = timezone.now()
            if provider_expiry_state == MetaProviderExpiryState.FINITE:
                if (
                    not isinstance(provider_expires_at, datetime)
                    or provider_expires_at <= validated_at
                ):
                    raise MetaAPIError("Meta USER token renewal validation failed.")
            elif (
                provider_expiry_state == MetaProviderExpiryState.NO_FINITE_EXPIRY
                and provider_expires_at is None
            ):
                pass
            else:
                raise MetaAPIError("Meta USER token renewal validation failed.")
            if (
                not isinstance(data_access_expires_at, datetime)
                or data_access_expires_at <= validated_at
            ):
                raise MetaAPIError("Meta USER token renewal validation failed.")

            # The client normalizes an omitted provider field to None and
            # rejects an explicitly supplied invalid value before returning.
            if (
                "expires_in" not in exchange_result
                or exchange_result.get("expires_in") is None
            ):
                token_expires_at = None
            else:
                expires_in = exchange_result.get("expires_in")
                if isinstance(expires_in, bool):
                    raise MetaAPIError(
                        "Meta USER token renewal validation failed."
                    )
                if isinstance(expires_in, str) and re.fullmatch(r"[0-9]+", expires_in):
                    expires_in = int(expires_in)
                if not isinstance(expires_in, int) or expires_in <= 0:
                    raise MetaAPIError(
                        "Meta USER token renewal validation failed."
                    )
                # Base this on request start so request/validation latency can
                # never extend the provider-reported lifetime locally.
                token_expires_at = exchange_started_at + timedelta(seconds=expires_in)
                if token_expires_at <= validated_at:
                    raise MetaAPIError("Meta USER token renewal validation failed.")

            encrypted_returned_token = encrypt_token(returned_token)
            updates = {
                "access_token": encrypted_returned_token,
                "token_expires_at": token_expires_at,
                "provider_token_type": "USER",
                "provider_is_valid": True,
                "provider_expiry_state": provider_expiry_state,
                "provider_expires_at": provider_expires_at,
                "data_access_expires_at": data_access_expires_at,
                "last_health_check_at": validated_at,
                "last_user_token_renewed_at": validated_at,
            }
            persistence_ready = True
        except MetaAccountCredential.DoesNotExist:
            return "skipped"
        except Exception as exc:
            if isinstance(exc, MetaAPIError):
                details = self.api.safe_error_metadata(exc)
                logger.warning(
                    "Meta USER token renewal did not complete. credential_id=%s "
                    "http_status=%s graph_error_code=%s graph_error_subcode=%s",
                    credential_id,
                    details["http_status"],
                    details["graph_error_code"],
                    details["graph_error_subcode"],
                )
            else:
                logger.warning(
                    "Meta USER token renewal failed safely. credential_id=%s error_type=%s",
                    credential_id,
                    type(exc).__name__,
                )
            return "retry"
        finally:
            if original_token is not None:
                del original_token
            if returned_token is not None:
                del returned_token
            if not persistence_ready:
                self._release_user_renewal_lock(str(credential_id), lock_token)

        try:
            with transaction.atomic():
                current = MetaAccountCredential.objects.select_for_update().get(
                    pk=credential_id,
                    credential_type=MetaCredentialType.USER,
                    status=MetaCredentialStatus.ACTIVE,
                    is_deleted=False,
                    social_connection__provider=SocialConnectionProvider.META,
                    social_connection__is_deleted=False,
                    social_connection__status=SocialConnectionStatus.ACTIVE,
                    provider_token_type="USER",
                )
                if (
                    current.provider_token_type != "USER"
                    or current.access_token != expected_access_token
                    or current.updated_at != expected_updated_at
                    or (
                        expected_organization_id is not None
                        and str(
                            getattr(
                                getattr(
                                    getattr(current, "social_connection", None),
                                    "organization",
                                    None,
                                ),
                                "organization_id",
                                "",
                            )
                            or ""
                        ).strip()
                        != expected_organization_id
                    )
                    or str(
                        getattr(
                            getattr(current, "social_connection", None),
                            "provider_user_id",
                            "",
                        )
                        or ""
                    ).strip()
                    != expected_user_id
                ):
                    return "stale"

                for field, value in updates.items():
                    setattr(current, field, value)
                current.save(
                    update_fields=[
                        *updates,
                        "updated_at",
                    ]
                )
            return "renewed"
        except MetaAccountCredential.DoesNotExist:
            return "stale"
        except Exception as exc:
            logger.warning(
                "Meta USER token renewal persistence failed safely. "
                "credential_id=%s error_type=%s",
                credential_id,
                type(exc).__name__,
            )
            return "retry"
        finally:
            if encrypted_returned_token is not None:
                del encrypted_returned_token
            self._release_user_renewal_lock(str(credential_id), lock_token)

    def _mark_parent_reconnect_needed(self, page_credential, error):
        parent = self._get_parent_user_credential(page_credential=page_credential)
        if parent is None:
            return
        details = self.api.safe_error_metadata(error)
        reconnect_status = (
            MetaCredentialStatus.INVALID
            if details["graph_error_code"] == 190
            else MetaCredentialStatus.ERROR
        )
        with transaction.atomic():
            parent = MetaAccountCredential.objects.select_for_update().get(pk=parent.pk)
            was_already_reconnect_required = parent.status in {
                MetaCredentialStatus.INVALID,
                MetaCredentialStatus.EXPIRED,
                MetaCredentialStatus.REVOKED,
                MetaCredentialStatus.ERROR,
            }
            parent.status = reconnect_status
            parent.save(update_fields=["status", "updated_at"])
            if not was_already_reconnect_required:
                self._record_parent_reconnect_required(parent)

    # ========================================================
    # REDIS DISTRIBUTED LOCK
    # ========================================================

    def _acquire_lock(
        self,
        credential_id: str,
    ) -> Optional[str]:
        """
        Prevent multiple Celery workers from processing the
        same Meta Page credential at the same time.
        """

        lock_key = f"meta:page-token-lifecycle:{credential_id}"

        lock_token = f"{credential_id}:" f"{timezone.now().timestamp()}"

        acquired = cache.add(
            lock_key,
            lock_token,
            timeout=self.LOCK_TIMEOUT_SECONDS,
        )

        if not acquired:
            return None

        return lock_token

    def _release_lock(
        self,
        credential_id: str,
        lock_token: str,
    ) -> None:
        """
        Release the Redis lock only when it still belongs
        to this lifecycle execution.
        """

        lock_key = f"meta:page-token-lifecycle:{credential_id}"

        try:
            redis_client = cache._cache.get_client(write=True)
            serialized_lock_token = cache._cache._serializer.dumps(lock_token)
            redis_client.eval(
                _RELEASE_LOCK_SCRIPT,
                1,
                cache.make_key(lock_key),
                serialized_lock_token,
            )

        except Exception:
            logger.error(
                "Failed to release Meta lifecycle lock. " "credential_id=%s",
                credential_id,
            )

    # ========================================================
    # ERROR CLASSIFICATION
    # ========================================================

    @staticmethod
    def _is_temporary_error(
        exc: MetaAPIError,
    ) -> bool:
        """
        Temporary errors must not cause a reconnect.

        Examples:
            429
            5xx
            timeout/network errors
            connection errors
        """

        status_code = getattr(
            exc,
            "status_code",
            None,
        )

        if status_code is None:
            return True

        if status_code == 429:
            return True

        if 500 <= status_code <= 599:
            return True

        return False

    @staticmethod
    def _is_authentication_error(
        exc: MetaAPIError,
    ) -> bool:
        """
        Detect errors that indicate the access token or
        authorization is no longer usable.
        """

        status_code = getattr(
            exc,
            "status_code",
            None,
        )

        if status_code in {
            400,
            401,
            403,
        }:
            return True

        message = str(exc).lower()

        authentication_keywords = (
            "invalid oauth",
            "access token",
            "expired",
            "oauth",
            "permission",
            "permissions",
            "authorization",
            "unauthorized",
            "not authorized",
            "session",
            "revoked",
        )

        return any(keyword in message for keyword in authentication_keywords)

    # ========================================================
    # VALIDATE PAGE TOKEN
    # ========================================================

    def _validate_page_token(
        self,
        *,
        page_id: str,
        page_access_token: str,
    ) -> dict:
        """
        Validate the currently stored Facebook Page token.

        We intentionally perform a real Page Graph API request
        instead of relying only on token expiry metadata.

        Successful response means the Page token is currently
        usable for that Page.
        """

        if not page_id:
            raise MetaAPIError(
                "Facebook Page ID is required.",
            )

        if not page_access_token:
            raise MetaAPIError(
                "Facebook Page access token is required.",
            )

        response = self.api.get(
            f"/{page_id}",
            access_token=page_access_token,
            params={
                "fields": "id,name",
            },
        )

        returned_page_id = str(
            response.get("id") or "",
        )

        if returned_page_id and returned_page_id != str(page_id):
            raise MetaAPIError(
                "Meta returned a different Facebook Page ID.",
                error_payload=response,
            )

        return response

    # ========================================================
    # GET PARENT META USER CREDENTIAL
    # ========================================================

    def _get_parent_user_credential(
        self,
        *,
        page_credential: MetaAccountCredential,
    ) -> Optional[MetaAccountCredential]:
        """
        PAGE credential intentionally does not have a direct
        social_connection.

        The parent connection is:

            Page Credential
                  ↓
            SocialAccount
                  ↓
            SocialAccount.connection
                  ↓
            SocialConnection
                  ↓
            USER Credential
        """

        social_account = page_credential.social_account

        if social_account is None:
            return None

        connection = social_account.connection

        if connection is None:
            return None

        try:
            # return get_meta_connection_credential(
            #     connection,
            # )
            return get_meta_connection_credential(
                social_connection=page_credential.social_account.connection,
            )

        except Exception:
            logger.error(
                "Unable to resolve parent Meta USER credential. "
                "page_credential_id=%s",
                page_credential.id,
            )

            return None

    # ========================================================
    # REISSUE PAGE TOKEN
    # ========================================================

    def _reissue_page_token(
        self,
        *,
        page_credential: MetaAccountCredential,
    ) -> str:
        """
        Request a fresh Facebook Page access token using
        the parent Meta USER access token.
        """

        social_account = page_credential.social_account

        if social_account is None:
            raise MetaAPIError(
                "Page credential is not linked to a SocialAccount.",
            )

        page_id = str(
            social_account.platform_account_id or "",
        ).strip()

        if not page_id:
            raise MetaAPIError(
                "Facebook Page ID is missing.",
            )

        user_credential = self._get_parent_user_credential(
            page_credential=page_credential,
        )

        if user_credential is None:
            raise MetaAPIError(
                "Parent Meta USER credential was not found.",
            )

        if user_credential.status != MetaCredentialStatus.ACTIVE:
            raise MetaAPIError(
                "Parent Meta USER credential is not active.",
            )

        if not user_credential.access_token:
            raise MetaAPIError(
                "Parent Meta USER credential has no access token.",
            )

        try:
            user_access_token = decrypt_token(
                user_credential.access_token,
            )

        except Exception as exc:
            logger.error(
                "Failed to decrypt Meta USER access token. " "credential_id=%s",
                user_credential.id,
            )

            raise MetaAPIError(
                "Unable to decrypt Meta USER access token.",
            ) from exc

        if not user_access_token:
            raise MetaAPIError(
                "Meta USER access token is empty.",
            )

        page_data = self.api.get_page(
            page_id=page_id,
            access_token=user_access_token,
        )

        new_page_token = page_data.get(
            "access_token",
        )

        if not new_page_token:
            raise MetaAPIError(
                "Meta did not return a new Facebook Page " "access token.",
                error_payload=page_data,
            )

        return str(new_page_token)

    # ========================================================
    # MARK SOCIAL ACCOUNT CONNECTED
    # ========================================================

    @staticmethod
    def _mark_account_connected(
        social_account: SocialAccount,
    ) -> None:
        """
        Restore the SocialAccount to a healthy state.
        """

        social_account.status = SocialAccountStatus.CONNECTED

        social_account.is_valid = True
        social_account.last_synced_at = timezone.now()

        social_account.save(
            update_fields=[
                "status",
                "is_valid",
                "last_synced_at",
                "updated_at",
            ],
        )

    # ========================================================
    # MARK SOCIAL ACCOUNT ERROR
    # ========================================================

    @staticmethod
    def _mark_account_error(
        social_account: SocialAccount,
    ) -> None:
        """
        Keep the SocialAccount record but mark it unhealthy.

        Frontend can use this state to show Reconnect.
        """

        social_account.status = SocialAccountStatus.ERROR

        social_account.is_valid = False
        social_account.last_synced_at = timezone.now()

        social_account.save(
            update_fields=[
                "status",
                "is_valid",
                "last_synced_at",
                "updated_at",
            ],
        )

    # ========================================================
    # SAVE VERIFIED PAGE TOKEN
    # ========================================================

    @transaction.atomic
    def _save_verified_page_token(
        self,
        *,
        credential_id: str,
        page_access_token: str,
    ) -> None:
        """
        Save a successfully verified/reissued Page token.

        Facebook Page token expiry is intentionally not inferred
        here. Current architecture stores token_expires_at=None
        for Page credentials.
        """

        # IMPORTANT:
        # Do not use select_related() together with select_for_update()
        # here because social_account is nullable.
        credential = MetaAccountCredential.objects.select_for_update().get(
            id=credential_id,
        )

        if credential.status == MetaCredentialStatus.REVOKED:
            return

        credential.access_token = encrypt_token(
            page_access_token,
        )

        credential.token_expires_at = None

        credential.status = MetaCredentialStatus.ACTIVE

        credential.last_verified_at = timezone.now()

        credential.save(
            update_fields=[
                "access_token",
                "token_expires_at",
                "status",
                "last_verified_at",
                "updated_at",
            ],
        )

        if credential.social_account:
            self._mark_account_connected(
                credential.social_account,
            )
            self._resolve_page_reconnect_required(credential)

    # ========================================================
    # MARK PAGE INVALID
    # ========================================================

    @transaction.atomic
    def _mark_page_invalid(
        self,
        *,
        credential_id: str,
    ) -> None:
        """
        Mark a Page credential invalid after recovery fails.

        Manual REVOKED state is never overwritten.
        """

        # IMPORTANT:
        # Lock only MetaAccountCredential.
        credential = MetaAccountCredential.objects.select_for_update().get(
            id=credential_id,
        )

        if credential.status == MetaCredentialStatus.REVOKED:
            return

        was_already_reconnect_required = credential.status in {
            MetaCredentialStatus.INVALID,
            MetaCredentialStatus.EXPIRED,
            MetaCredentialStatus.ERROR,
        }

        credential.status = MetaCredentialStatus.INVALID

        credential.last_verified_at = timezone.now()

        credential.save(
            update_fields=[
                "status",
                "last_verified_at",
                "updated_at",
            ],
        )

        if credential.social_account:
            self._mark_account_error(
                credential.social_account,
            )
            if not was_already_reconnect_required:
                MetaTokenLifecycleService._record_page_reconnect_required(credential)

    # ========================================================
    # PROCESS SINGLE PAGE CREDENTIAL
    # ========================================================

    def process_page_credential(
        self,
        credential: MetaAccountCredential,
    ) -> str:
        """
        Process one Facebook Page credential.

        Possible results:

            verified
            refreshed
            invalid
            retry
            revoked
            locked
            skipped
        """

        if credential.credential_type != MetaCredentialType.PAGE:
            return "skipped"

        if credential.status == MetaCredentialStatus.REVOKED:
            return "revoked"

        social_account = credential.social_account

        if social_account is None:
            return "skipped"

        if social_account.platform != "facebook":
            return "skipped"

        if social_account.is_deleted:
            return "skipped"

        page_id = str(
            social_account.platform_account_id or "",
        ).strip()

        if not page_id:
            return "skipped"

        lock_token = self._acquire_lock(
            str(credential.id),
        )

        if lock_token is None:
            return "locked"

        try:
            # Re-read after acquiring lock.
            #
            # IMPORTANT:
            # No select_related() here because this object may
            # later participate in select_for_update() operations
            # and both relationships are nullable.
            credential = MetaAccountCredential.objects.get(
                id=credential.id,
            )

            if credential.status == MetaCredentialStatus.REVOKED:
                return "revoked"

            if not credential.access_token:
                self._mark_page_invalid(
                    credential_id=str(
                        credential.id,
                    ),
                )

                return "invalid"

            # ------------------------------------------------
            # STEP 1
            # Validate existing Page token
            # ------------------------------------------------

            try:
                current_page_token = decrypt_token(
                    credential.access_token,
                )

            except Exception:
                logger.error(
                    "Failed to decrypt Facebook Page token. " "credential_id=%s",
                    credential.id,
                )

                self._mark_page_invalid(
                    credential_id=str(
                        credential.id,
                    ),
                )

                return "invalid"

            try:
                self._validate_page_token(
                    page_id=page_id,
                    page_access_token=current_page_token,
                )

                with transaction.atomic():

                    # IMPORTANT:
                    # Lock ONLY MetaAccountCredential.
                    locked_credential = (
                        MetaAccountCredential.objects.select_for_update().get(
                            id=credential.id,
                        )
                    )

                    if locked_credential.status == MetaCredentialStatus.REVOKED:
                        return "revoked"

                    locked_credential.status = MetaCredentialStatus.ACTIVE

                    locked_credential.last_verified_at = timezone.now()

                    locked_credential.save(
                        update_fields=[
                            "status",
                            "last_verified_at",
                            "updated_at",
                        ],
                    )

                    if locked_credential.social_account:
                        self._mark_account_connected(
                            locked_credential.social_account,
                        )
                        self._resolve_page_reconnect_required(locked_credential)

                return "verified"

            except MetaAPIError as exc:

                # Temporary Meta/network issue.
                if self._is_temporary_error(exc):
                    error_details = self.api.safe_error_metadata(exc)
                    logger.warning(
                        "Temporary Meta error while validating "
                        "Facebook Page token. "
                        "credential_id=%s http_status=%s "
                        "graph_error_code=%s graph_error_subcode=%s",
                        credential.id,
                        error_details["http_status"],
                        error_details["graph_error_code"],
                        error_details["graph_error_subcode"],
                    )

                    return "retry"

                # Unexpected non-authentication error.
                if not self._is_authentication_error(exc):
                    error_details = self.api.safe_error_metadata(exc)
                    logger.error(
                        "Unexpected Meta error while validating "
                        "Facebook Page token. "
                        "credential_id=%s http_status=%s "
                        "graph_error_code=%s graph_error_subcode=%s",
                        credential.id,
                        error_details["http_status"],
                        error_details["graph_error_code"],
                        error_details["graph_error_subcode"],
                    )

                    return "retry"

                # Authentication failure means we proceed
                # to Page token recovery.
                logger.warning(
                    "Facebook Page token appears invalid. "
                    "Attempting recovery. credential_id=%s",
                    credential.id,
                )

            # ------------------------------------------------
            # STEP 2
            # Recover Page token using USER token
            # ------------------------------------------------

            parent_credential = self._get_parent_user_credential(
                page_credential=credential,
            )
            if (
                parent_credential is None
                or parent_credential.status != MetaCredentialStatus.ACTIVE
            ):
                logger.warning(
                    "Facebook Page recovery deferred because parent Meta credential needs reconnect. credential_id=%s",
                    credential.id,
                )
                self._mark_page_invalid(
                    credential_id=str(credential.id),
                )
                return "invalid"

            try:
                new_page_token = self._reissue_page_token(
                    page_credential=credential,
                )
            except MetaAPIError as exc:
                if self._is_temporary_error(exc):
                    details = self.api.safe_error_metadata(exc)
                    logger.warning(
                    "Temporary Meta error while recovering Facebook Page token. "
                    "credential_id=%s http_status=%s graph_error_code=%s "
                    "graph_error_subcode=%s",
                    credential.id,
                    details["http_status"],
                    details["graph_error_code"],
                    details["graph_error_subcode"],
                    )
                    return "retry"
                if self._parent_error_is_definitive(exc):
                    self._mark_parent_reconnect_needed(credential, exc)
                    self._mark_page_invalid(
                        credential_id=str(credential.id),
                    )
                    details = self.api.safe_error_metadata(exc)
                    logger.warning(
                    "Parent Meta credential requires reconnect after Page recovery failure. "
                    "credential_id=%s http_status=%s graph_error_code=%s "
                    "graph_error_subcode=%s",
                    credential.id,
                    details["http_status"],
                    details["graph_error_code"],
                    details["graph_error_subcode"],
                    )
                    return "invalid"
                return "retry"

            try:
                # ------------------------------------------------
                # STEP 3
                # Validate newly issued token
                # ------------------------------------------------

                self._validate_page_token(
                    page_id=page_id,
                    page_access_token=new_page_token,
                )

                # ------------------------------------------------
                # STEP 4
                # Atomically save new token
                # ------------------------------------------------

                self._save_verified_page_token(
                    credential_id=str(
                        credential.id,
                    ),
                    page_access_token=new_page_token,
                )

                logger.info(
                    "Facebook Page token successfully recovered. "
                    "credential_id=%s page_id=%s",
                    credential.id,
                    page_id,
                )

                return "refreshed"

            except MetaAPIError as exc:

                if self._is_temporary_error(exc):
                    error_details = self.api.safe_error_metadata(exc)
                    logger.warning(
                        "Temporary Meta error while recovering "
                        "Facebook Page token. "
                        "credential_id=%s http_status=%s "
                        "graph_error_code=%s graph_error_subcode=%s",
                        credential.id,
                        error_details["http_status"],
                        error_details["graph_error_code"],
                        error_details["graph_error_subcode"],
                    )

                    return "retry"

                if self._is_authentication_error(exc):
                    error_details = self.api.safe_error_metadata(exc)
                    logger.warning(
                        "Facebook Page token recovery failed. "
                        "Reconnect required. "
                        "credential_id=%s http_status=%s "
                        "graph_error_code=%s graph_error_subcode=%s",
                        credential.id,
                        error_details["http_status"],
                        error_details["graph_error_code"],
                        error_details["graph_error_subcode"],
                    )

                    self._mark_page_invalid(
                        credential_id=str(
                            credential.id,
                        ),
                    )

                    return "invalid"

                error_details = self.api.safe_error_metadata(exc)
                logger.error(
                    "Unexpected Meta error during Page token "
                    "recovery. credential_id=%s http_status=%s "
                    "graph_error_code=%s graph_error_subcode=%s",
                    credential.id,
                    error_details["http_status"],
                    error_details["graph_error_code"],
                    error_details["graph_error_subcode"],
                )

                return "retry"

            except Exception:
                logger.error(
                    "Unexpected exception during Facebook "
                    "Page token lifecycle. credential_id=%s",
                    credential.id,
                )

                return "retry"

        finally:
            self._release_lock(
                str(credential.id),
                lock_token,
            )

    # ========================================================
    # PROCESS ALL ACTIVE FACEBOOK PAGE CREDENTIALS
    # ========================================================

    def refresh_due_credentials(self) -> Dict[str, int]:
        """
        Process all active Facebook Page credentials.

        Unlike Instagram, this does not use a 7-day expiry
        window.

        Every scheduled execution validates active Page tokens.
        Invalid tokens are recovered through their parent
        Meta USER credential when possible.
        """

        result = {
            "checked": 0,
            "verified": 0,
            "refreshed": 0,
            "valid": 0,
            "invalid": 0,
            "revoked": 0,
            "retry": 0,
            "reconnect_needed": 0,
            "parent_checked": 0,
            "parent_valid": 0,
            "parent_invalid": 0,
            "parent_retry": 0,
            "skipped": 0,
            "locked": 0,
        }

        credentials = (
            MetaAccountCredential.objects.select_related(
                "social_account",
                "social_account__connection",
            )
            .filter(
                credential_type=MetaCredentialType.PAGE,
                status=MetaCredentialStatus.ACTIVE,
                social_account__isnull=False,
                social_account__is_deleted=False,
                social_account__platform="facebook",
            )
            .order_by("id")
        )

        # Resolve each selected parent USER credential once, then run a single
        # health probe per credential for this maintenance cycle.
        parents = {}
        for page_credential in credentials.iterator(chunk_size=200):
            parent = self._get_parent_user_credential(page_credential=page_credential)
            if parent:
                parents.setdefault(str(parent.id), parent)
        reconnect_parent_ids = set()
        for parent_id, parent in parents.items():
            if parent.status != MetaCredentialStatus.ACTIVE:
                if parent.status in {
                    MetaCredentialStatus.EXPIRED,
                    MetaCredentialStatus.REVOKED,
                    MetaCredentialStatus.INVALID,
                    MetaCredentialStatus.ERROR,
                }:
                    result["parent_invalid"] += 1
                    result["invalid"] += 1
                    reconnect_parent_ids.add(parent_id)
                continue
            result["parent_checked"] += 1
            result["checked"] += 1
            parent_outcome = self._check_parent_user_credential(parent)
            if parent_outcome == "valid":
                result["parent_valid"] += 1
                result["valid"] += 1
            elif parent_outcome == "reconnect_needed":
                result["parent_invalid"] += 1
                result["invalid"] += 1
                reconnect_parent_ids.add(parent_id)
            else:
                result["parent_retry"] += 1
                result["retry"] += 1

        for credential in credentials.iterator(chunk_size=200):
            result["checked"] += 1

            try:
                outcome = self.process_page_credential(
                    credential,
                )

            except Exception:
                logger.error("Unhandled Meta lifecycle error. credential_id=%s", credential.id)

                result["retry"] += 1
                continue

            if outcome in {
                "verified",
                "refreshed",
                "invalid",
                "revoked",
                "retry",
                "skipped",
                "locked",
            }:
                result[outcome] += 1

            if outcome in {"verified", "refreshed"}:
                result["valid"] += 1
            elif outcome == "reconnect_needed":
                parent = self._get_parent_user_credential(page_credential=credential)
                if parent:
                    reconnect_parent_ids.add(str(parent.id))
                else:
                    connection_id = getattr(credential.social_account, "connection_id", None)
                    reconnect_parent_ids.add(f"missing-parent:{connection_id or credential.id}")

        # Parent failures make this run partial even when the Page-token probe
        # itself did not need recovery.
        result["reconnect_needed"] = len(reconnect_parent_ids)

        logger.info(
            "Meta Facebook Page token lifecycle completed: %s",
            result,
        )

        return result

    @staticmethod
    def _data_access_warning_stage(expires_at, *, now):
        """Return the current warning stage for an aware expiry timestamp."""
        if expires_at is None:
            return None
        if timezone.is_naive(expires_at):
            expires_at = timezone.make_aware(
                expires_at,
                timezone.get_current_timezone(),
            )
        if expires_at <= now:
            return "expired"
        remaining = expires_at - now
        if remaining <= META_USER_DATA_ACCESS_URGENT_WINDOW:
            return "3d"
        if remaining <= META_USER_DATA_ACCESS_WARNING_WINDOW:
            return "14d"
        return None

    def _apply_user_data_access_expiry_policy(
        self, *, connection, expires_at, now
    ):
        """Apply idempotent notification state for one locked Meta connection."""
        from apps.notifications.services import (
            record_meta_user_data_access_expiry_warning,
            record_social_credential_reconnect_required,
            resolve_meta_user_data_access_expiry_warnings,
        )

        stage = self._data_access_warning_stage(expires_at, now=now)
        if stage == "expired":
            resolve_meta_user_data_access_expiry_warnings(
                connection_id=connection.pk,
                organization=connection.organization,
            )
            record_social_credential_reconnect_required(
                organization=connection.organization,
                scope="meta-connection",
                subject_id=connection.pk,
                platform="facebook",
            )
            return "expired"
        if stage == "3d":
            resolve_meta_user_data_access_expiry_warnings(
                connection_id=connection.pk,
                organization=connection.organization,
                stage="14d",
            )
            record_meta_user_data_access_expiry_warning(
                organization=connection.organization,
                connection_id=connection.pk,
                stage="3d",
                expires_at=expires_at,
            )
            return "urgent"
        if stage == "14d":
            resolve_meta_user_data_access_expiry_warnings(
                connection_id=connection.pk,
                organization=connection.organization,
                stage="3d",
            )
            record_meta_user_data_access_expiry_warning(
                organization=connection.organization,
                connection_id=connection.pk,
                stage="14d",
                expires_at=expires_at,
            )
            return "warning"

        resolve_meta_user_data_access_expiry_warnings(
            connection_id=connection.pk,
            organization=connection.organization,
        )
        return "missing_expiry" if expires_at is None else "resolved"

    def monitor_user_data_access_expiry(self, *, now=None) -> Dict[str, int]:
        """Reconcile stored Meta USER data-access deadlines without provider calls."""
        from apps.notifications.models import UserNotification, UserNotificationType
        from apps.notifications.services import (
            META_USER_DATA_ACCESS_EXPIRY_EVENT_PREFIX as notification_prefix,
            resolve_meta_user_data_access_expiry_warnings,
        )

        now = now or timezone.now()
        if timezone.is_naive(now):
            now = timezone.make_aware(now, timezone.get_current_timezone())

        active_connections = {}
        connection_rows = (
            MetaAccountCredential.objects.filter(
                credential_type=MetaCredentialType.USER,
                status=MetaCredentialStatus.ACTIVE,
                is_deleted=False,
                social_connection__isnull=False,
                social_connection__provider=SocialConnectionProvider.META,
                social_connection__status=SocialConnectionStatus.ACTIVE,
                social_connection__is_deleted=False,
            )
            .order_by("social_connection_id", "-updated_at", "-created_at", "-id")
            .values("social_connection_id", "social_connection__organization_id")
        )
        for row in connection_rows.iterator(chunk_size=200):
            active_connections.setdefault(
                str(row["social_connection_id"]),
                row["social_connection__organization_id"],
            )

        # Resolve warnings for connections whose USER credential was removed,
        # revoked, disconnected, soft-deleted, or moved to another organization.
        pending_warnings = UserNotification.objects.filter(
            event_type=UserNotificationType.META_USER_DATA_ACCESS_EXPIRING,
            is_deleted=False,
            resolved_at__isnull=True,
            event_key__startswith=f"{notification_prefix}:",
        ).values("event_key", "organization_id")
        resolved = 0
        for warning in pending_warnings.iterator(chunk_size=200):
            parts = warning["event_key"].split(":")
            if len(parts) != 3 or parts[0] != notification_prefix:
                continue
            connection_id = parts[1]
            active_organization_id = active_connections.get(connection_id)
            if active_organization_id is None or str(active_organization_id) != str(
                warning["organization_id"]
            ):
                resolved += resolve_meta_user_data_access_expiry_warnings(
                    connection_id=connection_id,
                    organization_id=warning["organization_id"],
                )

        result = {
            "checked": 0,
            "warning": 0,
            "urgent": 0,
            "expired": 0,
            "missing_expiry": 0,
            "resolved": resolved,
            "skipped": 0,
        }
        for raw_connection_id, organization_id in active_connections.items():
            with transaction.atomic():
                connection = (
                    SocialConnection.objects.select_for_update()
                    .select_related("organization")
                    .filter(
                        pk=raw_connection_id,
                        organization_id=organization_id,
                        provider=SocialConnectionProvider.META,
                        status=SocialConnectionStatus.ACTIVE,
                        is_deleted=False,
                    )
                    .first()
                )
                if connection is None:
                    result["resolved"] += resolve_meta_user_data_access_expiry_warnings(
                        connection_id=raw_connection_id,
                        organization_id=organization_id,
                    )
                    result["skipped"] += 1
                    continue

                # Select only metadata fields; the encrypted access_token is
                # never loaded, decrypted, or passed to this monitor.
                credential = (
                    MetaAccountCredential.objects.select_for_update()
                    .filter(
                        social_connection=connection,
                        credential_type=MetaCredentialType.USER,
                        status=MetaCredentialStatus.ACTIVE,
                        is_deleted=False,
                    )
                    .order_by("-updated_at", "-created_at", "-id")
                    .values("data_access_expires_at")
                    .first()
                )
                if credential is None:
                    result["resolved"] += resolve_meta_user_data_access_expiry_warnings(
                        connection_id=connection.pk,
                        organization=connection.organization,
                    )
                    result["skipped"] += 1
                    continue

                result["checked"] += 1
                expires_at = credential["data_access_expires_at"]
                action = self._apply_user_data_access_expiry_policy(
                    connection=connection,
                    expires_at=expires_at,
                    now=now,
                )
                if action in {"expired", "urgent", "warning", "missing_expiry"}:
                    result[action] += 1

        logger.info("Meta USER data-access expiry monitoring completed: %s", result)
        return result
