import json
from urllib.parse import urlsplit, urlunsplit

from apps.integrations.instagram.client import InstagramAPIClient
from apps.integrations.instagram.crypto import decrypt_token as decrypt_instagram_token
from apps.integrations.instagram.exceptions import InstagramAPIError
from apps.integrations.instagram.selectors import get_active_instagram_credential
from apps.integrations.meta.client import MetaAPIClient
from apps.integrations.meta.credentials import MetaCredentialService

from .base import BasePublisher
from .exceptions import (
    MediaProcessingPending,
    ProviderPublishingError,
    PublishingValidationError,
)


class MetaPublisher(BasePublisher):
    """Publish one destination without duplicating credential management."""

    def publish(self, *, post_platform):
        account = post_platform.social_account
        if not account:
            raise PublishingValidationError("Social account is required for publishing.")
        if account.platform == "facebook":
            return self.publish_facebook(post_platform=post_platform)
        if account.platform == "instagram":
            return self.publish_instagram(post_platform=post_platform)
        raise PublishingValidationError("Meta supports Facebook and Instagram only.")

    @staticmethod
    def _media(post_platform):
        media = list(post_platform.post.media.filter(is_deleted=False).order_by("sort_order"))
        if not media or any(not item.file or not item.file.url.startswith("https://") for item in media):
            raise PublishingValidationError("Publishing requires secure, public media URLs.")
        return media

    @staticmethod
    def _instagram_media_url(media):
        """Return an Instagram-fetchable Cloudinary delivery URL."""

        url = media.file.url

        if media.media_type != "IMAGE":
            return url

        parsed = urlsplit(url)
        filename = parsed.path.rsplit("/", 1)[-1]
        if "." in filename:
            return url

        mime_type = (media.mime_type or "").lower()
        extension = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
        }.get(mime_type, "jpg")

        return urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                f"{parsed.path}.{extension}",
                parsed.query,
                parsed.fragment,
            )
        )

    @staticmethod
    def _retry_unavailable_instagram_image(exc):
        """Route Meta's transient image-fetch rejection through existing retry."""

        error = getattr(exc, "error_payload", {}).get("error", {})
        if str(error.get("code")) == "9004":
            raise MediaProcessingPending(
                "Instagram image media is not available for processing yet."
            ) from exc
        raise exc

    def publish_facebook(self, *, post_platform):
        account = post_platform.social_account
        token = MetaCredentialService.get_access_token(social_account=account)
        media, api, caption = self._media(post_platform), MetaAPIClient(), post_platform.post.caption
        content_type = (post_platform.content_type or "POST").upper()
        reel_video_id = None
        if content_type == "REEL":
            if len(media) != 1 or media[0].media_type != "VIDEO":
                raise PublishingValidationError("Facebook Reels require exactly one video.")
            reel_media = media[0]
            started = api.post(
                f"/{account.platform_account_id}/video_reels",
                access_token=token,
                data={"upload_phase": "START"},
            )
            video_id = started.get("video_id")
            upload_url = started.get("upload_url")
            if not video_id or not upload_url:
                raise ProviderPublishingError(
                    "Facebook did not return a Reel upload session."
                )
            reel_video_id = str(video_id)
            reel_media.file.open("rb")
            try:
                api.upload_reel_video(
                    upload_url,
                    access_token=token,
                    video_file=reel_media.file,
                    file_size=reel_media.file_size or reel_media.file.size,
                )
            finally:
                reel_media.file.close()
            result = api.post(
                f"/{account.platform_account_id}/video_reels",
                access_token=token,
                data={
                    "upload_phase": "FINISH",
                    "video_id": str(video_id),
                    "video_state": "PUBLISHED",
                    "description": caption,
                },
            )
        elif content_type == "STORY":
            if len(media) != 1:
                raise PublishingValidationError(
                    "Facebook Stories require exactly one media file."
                )
            if media[0].media_type == "VIDEO":
                story_media = media[0]
                started = api.post(
                    f"/{account.platform_account_id}/video_stories",
                    access_token=token,
                    data={"upload_phase": "START"},
                )
                video_id = started.get("video_id")
                upload_url = started.get("upload_url")
                if not video_id or not upload_url:
                    raise ProviderPublishingError(
                        "Facebook did not return a Story video upload session."
                    )
                story_media.file.open("rb")
                try:
                    api.upload_reel_video(
                        upload_url,
                        access_token=token,
                        video_file=story_media.file,
                        file_size=story_media.file_size or story_media.file.size,
                    )
                finally:
                    story_media.file.close()
                result = api.post(
                    f"/{account.platform_account_id}/video_stories",
                    access_token=token,
                    data={
                        "upload_phase": "FINISH",
                        "video_id": str(video_id),
                        "video_state": "PUBLISHED",
                    },
                )
            elif media[0].media_type != "IMAGE":
                raise PublishingValidationError(
                    "Facebook Stories require an image or video media file."
                )
            else:
                uploaded = api.post(
                    f"/{account.platform_account_id}/photos",
                    access_token=token,
                    data={"url": media[0].file.url, "published": "false"},
                )
                photo_id = uploaded.get("id")
                if not photo_id:
                    raise ProviderPublishingError(
                        "Facebook did not return a Story photo ID."
                    )
                result = api.post(
                    f"/{account.platform_account_id}/photo_stories",
                    access_token=token,
                    data={"photo_id": str(photo_id)},
                )
        elif len(media) == 1 and media[0].media_type == "IMAGE":
            result = api.post(f"/{account.platform_account_id}/photos", access_token=token,
                              data={"url": media[0].file.url, "caption": caption})
        elif len(media) == 1 and media[0].media_type == "VIDEO":
            result = api.post(f"/{account.platform_account_id}/videos", access_token=token,
                              data={"file_url": media[0].file.url, "description": caption})
        elif all(item.media_type == "IMAGE" for item in media):
            attachments = []
            for item in media:
                uploaded = api.post(f"/{account.platform_account_id}/photos", access_token=token,
                                    data={"url": item.file.url, "published": "false"})
                if not uploaded.get("id"):
                    raise ProviderPublishingError("Facebook did not return an uploaded media ID.")
                attachments.append({"media_fbid": uploaded["id"]})
            result = api.post(f"/{account.platform_account_id}/feed", access_token=token,
                              data={"message": caption, "attached_media": json.dumps(attachments)})
        else:
            raise PublishingValidationError("Facebook mixed-media publishing is not supported.")
        external_id = result.get("post_id") or result.get("id") or reel_video_id
        if not external_id:
            raise ProviderPublishingError("Facebook did not return a publication ID.")
        return {"external_post_id": str(external_id)}

    def publish_instagram(self, *, post_platform):
        account = post_platform.social_account
        credential = get_active_instagram_credential(social_account=account)
        if not credential:
            raise PublishingValidationError("Instagram credential is not active.")
        token = decrypt_instagram_token(credential.encrypted_access_token)
        api = InstagramAPIClient()
        media = self._media(post_platform)
        content_type = (post_platform.content_type or "POST").upper()

        if len(media) > 1:
            if content_type not in {"POST", "CAROUSEL"}:
                raise PublishingValidationError(
                    "Instagram Stories and Reels require exactly one media file."
                )

            child_ids = post_platform.provider_state.get("carousel_children", [])
            if len(child_ids) < len(media):
                for item in media[len(child_ids) :]:
                    source = "image_url" if item.media_type == "IMAGE" else "video_url"
                    try:
                        child = api.graph_post(
                            f"{account.platform_account_id}/media",
                            access_token=token,
                            data={
                                source: self._instagram_media_url(item),
                                "is_carousel_item": "true",
                            },
                        )
                    except InstagramAPIError as exc:
                        if item.media_type == "IMAGE":
                            self._retry_unavailable_instagram_image(exc)
                        raise
                    if not child.get("id"):
                        raise ProviderPublishingError(
                            "Instagram did not return a child container ID."
                        )
                    child_ids.append(str(child["id"]))
                    post_platform.provider_state = {
                        **post_platform.provider_state,
                        "carousel_children": child_ids,
                    }
                    post_platform.save(update_fields=["provider_state", "updated_at"])
                raise MediaProcessingPending("Instagram carousel media is still processing.")

            for child_id in child_ids:
                state = api.graph_get(
                    child_id,
                    access_token=token,
                    params={"fields": "status_code"},
                )
                if state.get("status_code") not in {"FINISHED", "PUBLISHED"}:
                    raise MediaProcessingPending(
                        "Instagram carousel media is still processing."
                    )

            if not post_platform.provider_container_id:
                container = api.graph_post(
                    f"{account.platform_account_id}/media",
                    access_token=token,
                    data={
                        "media_type": "CAROUSEL",
                        "children": ",".join(child_ids),
                        "caption": post_platform.post.caption,
                    },
                )
                container_id = container.get("id")
                if not container_id:
                    raise ProviderPublishingError(
                        "Instagram did not return a carousel container ID."
                    )
                post_platform.provider_container_id = str(container_id)
                post_platform.save(
                    update_fields=["provider_container_id", "updated_at"]
                )
                raise MediaProcessingPending("Instagram carousel is still processing.")
        else:
            item = media[0]
            if content_type == "REEL" and item.media_type != "VIDEO":
                raise PublishingValidationError("Instagram Reels require exactly one video.")
            if content_type not in {"POST", "REEL", "STORY"}:
                raise PublishingValidationError("Unsupported Instagram content type.")

            if post_platform.provider_container_id:
                return self._publish_instagram_container(
                    api=api,
                    token=token,
                    account_id=account.platform_account_id,
                    post_platform=post_platform,
                )

            source = "image_url" if media[0].media_type == "IMAGE" else "video_url"
            payload = {
                source: self._instagram_media_url(item),
                "caption": post_platform.post.caption,
            }

            # Instagram image posts use the image_url container contract.
            # Supplying media_type=IMAGE makes this endpoint reject the
            # request as unsupported. Only non-image media requires an
            # explicit media type.
            if content_type == "REEL":
                payload["media_type"] = "REELS"
            elif content_type == "STORY":
                payload["media_type"] = "STORIES"
            elif media[0].media_type == "VIDEO":
                payload["media_type"] = "REELS"

            try:
                container = api.graph_post(
                    f"{account.platform_account_id}/media",
                    access_token=token,
                    data=payload,
                )
            except InstagramAPIError as exc:
                if item.media_type == "IMAGE":
                    self._retry_unavailable_instagram_image(exc)
                raise
            container_id = container.get("id")
            if not container_id:
                raise ProviderPublishingError("Instagram did not return a media container ID.")
            post_platform.provider_container_id = str(container_id)
            post_platform.save(update_fields=["provider_container_id", "updated_at"])

            # Preserve the established single-image feed flow. Images are
            # immediately eligible for the status check; video-derived
            # containers continue through the retry/resume path below.
            if content_type == "POST" and item.media_type == "IMAGE":
                return self._publish_instagram_container(
                    api=api,
                    token=token,
                    account_id=account.platform_account_id,
                    post_platform=post_platform,
                )

            raise MediaProcessingPending("Instagram media is still processing.")

        return self._publish_instagram_container(
            api=api,
            token=token,
            account_id=account.platform_account_id,
            post_platform=post_platform,
        )

    @staticmethod
    def _publish_instagram_container(*, api, token, account_id, post_platform):
        container_id = post_platform.provider_container_id
        state = api.graph_get(container_id, access_token=token, params={"fields": "status_code"})
        if state.get("status_code") not in {"FINISHED", "PUBLISHED"}:
            raise MediaProcessingPending("Instagram media is still processing.")
        result = api.graph_post(
            f"{account_id}/media_publish",
            access_token=token,
            data={"creation_id": str(container_id)},
        )
        if not result.get("id"):
            raise ProviderPublishingError("Instagram did not return a publication ID.")
        return {"external_post_id": str(result["id"]), "provider_container_id": str(container_id)}
