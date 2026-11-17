from datetime import timedelta
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from apps.common.throttles import RedisRateThrottle

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.social_accounts.models import SocialAccount, SocialPlatform
from rest_framework.exceptions import ValidationError

from .models import (
    MediaUploadSession,
    MediaUploadStatus,
    Post,
    PostMediaType,
    PostPublishType,
)
from .serializers import MediaUploadSessionCreateSerializer, PostMediaInputSerializer
from .publishing.meta import MetaPublisher
from .tasks import cleanup_expired_media_upload_sessions_task
from .services import (
    MediaUploadValidationError,
    create_post,
    validate_multipart_media_for_targets,
    validate_media_assets_for_targets,
)
from .storage import PostMediaCloudinaryStorage
from .views import (
    OrganizationMediaUploadSessionAPIView,
    OrganizationPostPublishNowAPIView,
    OrganizationPostTargetPublishNowAPIView,
    OrganizationPostTargetRetryAPIView,
)


@override_settings(
    MEDIA_UPLOAD_MAX_IMAGE_BYTES=10_000_000,
    MEDIA_UPLOAD_MAX_VIDEO_BYTES=100_000_000,
)
class UploadSizeLimitSerializerTests(SimpleTestCase):
    def test_upload_session_serializer_accepts_exact_limits(self):
        image = MediaUploadSessionCreateSerializer(data={
            "filename": "image.png",
            "content_type": "image/png",
            "size": 10_000_000,
        })
        video = MediaUploadSessionCreateSerializer(data={
            "filename": "video.mp4",
            "content_type": "video/mp4",
            "size": 100_000_000,
        })

        self.assertTrue(image.is_valid(), image.errors)
        self.assertTrue(video.is_valid(), video.errors)

    def test_upload_session_serializer_rejects_one_byte_over_limits(self):
        for content_type, filename, size in (
            ("image/png", "image.png", 10_000_001),
            ("video/mp4", "video.mp4", 100_000_001),
        ):
            with self.subTest(content_type=content_type):
                serializer = MediaUploadSessionCreateSerializer(data={
                    "filename": filename,
                    "content_type": content_type,
                    "size": size,
                })
                self.assertFalse(serializer.is_valid())
                self.assertIn("size", serializer.errors)


    def test_legacy_multipart_serializers_use_exact_byte_limits(self):
        image_bytes = BytesIO()
        from PIL import Image

        Image.new("RGB", (1, 1), color="white").save(image_bytes, format="PNG")
        image_file = SimpleUploadedFile(
            "image.png",
            image_bytes.getvalue(),
            content_type="image/png",
        )
        image_file.size = 10_000_000

        video_file = SimpleUploadedFile(
            "video.mp4",
            b"video",
            content_type="video/mp4",
        )
        video_file.size = 100_000_000

        serializer = PostMediaInputSerializer()
        serializer.validate_image(image_file)
        serializer.validate_video(video_file)

    def test_legacy_multipart_serializers_reject_one_byte_over_limits(self):
        image_file = SimpleUploadedFile(
            "image.png",
            b"not-read-because-size-is-over-limit",
            content_type="image/png",
        )
        image_file.size = 10_000_001
        video_file = SimpleUploadedFile(
            "video.mp4",
            b"video",
            content_type="video/mp4",
        )
        video_file.size = 100_000_001

        serializer = PostMediaInputSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_image(image_file)
        with self.assertRaises(ValidationError):
            serializer.validate_video(video_file)


class InMemoryAtomicRedis:
    """Deterministic in-memory stand-in for Redis rate-limit EVAL."""

    def __init__(self):
        self.counters = {}
        self.keys_seen = []

    def eval(self, _script, key_count, *keys_and_windows):
        keys = keys_and_windows[:key_count]
        windows_ms = keys_and_windows[key_count:]
        self.keys_seen.extend(keys)
        values = []
        for key, window_ms in zip(keys, windows_ms):
            count, ttl = self.counters.get(key, (0, window_ms))
            count += 1
            self.counters[key] = (count, ttl)
            values.extend((count, ttl))
        return values


@override_settings(
    DMC_RATE_LIMITS={
        "media_upload_create": ((20, 60),),
        "media_upload_finalize": ((30, 60),),
        "media_upload_finalize_session": ((5, 60),),
    },
    DMC_RATE_LIMIT_REDIS_FAILURE_POLICY="closed",
)
class MediaUploadRateLimitTests(SimpleTestCase):
    databases = set()

    def setUp(self):
        self.factory = APIRequestFactory()
        self.redis = InMemoryAtomicRedis()
        self.redis_patcher = patch.object(
            RedisRateThrottle,
            "_redis_client",
            return_value=self.redis,
        )
        self.redis_patcher.start()
        self.addCleanup(self.redis_patcher.stop)
        self.user = SimpleNamespace(pk="synthetic-user", is_authenticated=True)
        self.view = OrganizationMediaUploadSessionAPIView.as_view()

    def dispatch(
        self,
        method,
        organization_id="ORG-TEST",
        session_id=None,
        user=None,
    ):
        request = getattr(self.factory, method.lower())("/upload/", {}, format="json")
        force_authenticate(request, user=user or self.user)
        kwargs = {"organization_id": organization_id}
        if session_id is not None:
            kwargs["session_id"] = session_id
        handler = Response({"accepted": True})
        with patch.object(
            OrganizationMediaUploadSessionAPIView,
            method.lower(),
            return_value=handler,
        ):
            return self.view(request, **kwargs)

    def post(self, organization_id="ORG-TEST", session_id=None):
        return self.dispatch("POST", organization_id, session_id)

    def test_create_limit_is_20_per_minute_per_user_and_organization(self):
        responses = [self.post() for _ in range(21)]

        self.assertTrue(all(response.status_code == 200 for response in responses[:20]))
        self.assertEqual(responses[20].status_code, 429)
        self.assertIn("Retry-After", responses[20])
        self.assertEqual(int(responses[20]["Retry-After"]), 60)

    def test_finalize_limit_is_30_per_minute_per_user_and_organization(self):
        responses = [
            self.post(session_id=f"session-{index}")
            for index in range(31)
        ]

        self.assertTrue(all(response.status_code == 200 for response in responses[:30]))
        self.assertEqual(responses[30].status_code, 429)
        self.assertEqual(int(responses[30]["Retry-After"]), 60)

    def test_finalize_has_a_separate_per_session_burst_limit(self):
        responses = [
            self.post(session_id="session-one")
            for _ in range(6)
        ]

        self.assertTrue(all(response.status_code == 200 for response in responses[:5]))
        self.assertEqual(responses[5].status_code, 429)
        self.assertIn("Retry-After", responses[5])
        self.assertEqual(self.post(session_id="session-two").status_code, 200)

    def test_user_and_organization_identifiers_have_independent_buckets(self):
        first_user_responses = [
            self.post(organization_id="ORG-ONE")
            for _ in range(20)
        ]

        self.assertEqual(first_user_responses[-1].status_code, 200)
        self.assertEqual(self.post(organization_id="ORG-TWO").status_code, 200)
        other_user = SimpleNamespace(pk="other-user", is_authenticated=True)
        self.assertEqual(
            self.dispatch("POST", organization_id="ORG-ONE", user=other_user).status_code,
            200,
        )

    def test_rate_limit_keys_hash_user_organization_and_session_identifiers(self):
        self.post(organization_id="private-org", session_id="private-session")

        self.assertEqual(len(self.redis.keys_seen), 2)
        for key in self.redis.keys_seen:
            self.assertTrue(key.startswith("dmc:ratelimit:v1:media_upload_"))
            self.assertNotIn("private-org", key)
            self.assertNotIn("private-session", key)
            self.assertNotIn("synthetic-user", key)

    def test_session_get_is_not_limited_by_create_or_finalize_post_scopes(self):
        self.dispatch("GET", session_id="session-one")

        self.assertEqual(self.redis.keys_seen, [])


@override_settings(
    DMC_RATE_LIMITS={
        "publish_now": ((5, 60),),
        "publish_target_now": ((5, 60),),
        "publish_retry": ((3, 60), (20, 3600)),
    },
    DMC_RATE_LIMIT_REDIS_FAILURE_POLICY="closed",
)
class PublishingRateLimitTests(SimpleTestCase):
    databases = set()

    def setUp(self):
        self.factory = APIRequestFactory()
        self.redis = InMemoryAtomicRedis()
        self.redis_patcher = patch.object(
            RedisRateThrottle,
            "_redis_client",
            return_value=self.redis,
        )
        self.redis_patcher.start()
        self.addCleanup(self.redis_patcher.stop)
        self.user = SimpleNamespace(pk="synthetic-publisher", is_authenticated=True)

    def call_action(
        self,
        view_class,
        *throttle_dimension_args,
        organization_id="ORG-TEST",
        user=None,
    ):
        request = self.factory.post("/publish/", {}, format="json")
        force_authenticate(request, user=user or self.user)
        kwargs = {
            "organization_id": organization_id,
            "post_id": "synthetic-post",
        }
        if throttle_dimension_args:
            kwargs["target_id"] = throttle_dimension_args[0]
        view = view_class.as_view()
        handler = Response({"accepted": True})
        with patch.object(view_class, "post", return_value=handler):
            return view(request, **kwargs)

    def test_aggregate_publish_now_is_limited_to_five_per_user_organization(self):
        responses = [
            self.call_action(OrganizationPostPublishNowAPIView)
            for _ in range(6)
        ]

        self.assertTrue(all(response.status_code == 200 for response in responses[:5]))
        self.assertEqual(responses[5].status_code, 429)
        self.assertEqual(int(responses[5]["Retry-After"]), 60)

    def test_target_publish_now_is_limited_to_five_per_user_organization(self):
        responses = [
            self.call_action(
                OrganizationPostTargetPublishNowAPIView,
                "target-one",
            )
            for _ in range(6)
        ]

        self.assertTrue(all(response.status_code == 200 for response in responses[:5]))
        self.assertEqual(responses[5].status_code, 429)
        self.assertEqual(int(responses[5]["Retry-After"]), 60)

    def test_publish_now_counters_are_scoped_to_user_and_organization(self):
        limited = [
            self.call_action(OrganizationPostPublishNowAPIView)
            for _ in range(6)
        ]

        self.assertEqual(limited[-1].status_code, 429)
        self.assertEqual(
            self.call_action(
                OrganizationPostPublishNowAPIView,
                organization_id="ORG-OTHER",
            ).status_code,
            200,
        )
        other_user = SimpleNamespace(pk="other-publisher", is_authenticated=True)
        self.assertEqual(
            self.call_action(
                OrganizationPostPublishNowAPIView,
                user=other_user,
            ).status_code,
            200,
        )

    def test_retry_is_limited_to_three_per_minute_per_target(self):
        responses = [
            self.call_action(OrganizationPostTargetRetryAPIView, "target-one")
            for _ in range(4)
        ]

        self.assertTrue(all(response.status_code == 200 for response in responses[:3]))
        self.assertEqual(responses[3].status_code, 429)
        self.assertEqual(int(responses[3]["Retry-After"]), 60)
        self.assertEqual(
            self.call_action(OrganizationPostTargetRetryAPIView, "target-two").status_code,
            200,
        )

    def test_retry_is_limited_to_twenty_per_hour_per_user_organization(self):
        responses = [
            self.call_action(
                OrganizationPostTargetRetryAPIView,
                f"target-{index}",
            )
            for index in range(21)
        ]

        self.assertTrue(all(response.status_code == 200 for response in responses[:20]))
        self.assertEqual(responses[20].status_code, 429)
        self.assertGreater(int(responses[20]["Retry-After"]), 60)

    def test_publishing_rate_limit_keys_hash_all_subject_identifiers(self):
        self.call_action(
            OrganizationPostTargetRetryAPIView,
            "private-target-id",
            organization_id="private-organization-id",
        )

        self.assertEqual(len(self.redis.keys_seen), 2)
        for key in self.redis.keys_seen:
            self.assertTrue(key.startswith("dmc:ratelimit:v1:publish_retry:"))
            self.assertNotIn("private-target-id", key)
            self.assertNotIn("private-organization-id", key)
            self.assertNotIn("synthetic-publisher", key)


class UploadPolicyEndpointTests(SimpleTestCase):
    @override_settings(
        MEDIA_UPLOAD_MAX_IMAGE_BYTES=12_345_678,
        MEDIA_UPLOAD_MAX_VIDEO_BYTES=98_765_432,
    )
    def test_authenticated_policy_endpoint_returns_effective_overrides(self):
        client = APIClient()
        client.force_authenticate(user=SimpleNamespace(is_authenticated=True))

        response = client.get("/api/posts/media-upload-policy/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], {
            "image_max_size_bytes": 12_345_678,
            "video_max_size_bytes": 98_765_432,
        })


class CloudinaryStreamingStorageTests(SimpleTestCase):
    @override_settings(MEDIA_UPLOAD_CHUNK_SIZE_BYTES=8 * 1024 * 1024)
    @patch("apps.posts.storage.uploader.upload")
    @patch("apps.posts.storage.uploader.upload_large")
    def test_video_fallback_upload_uses_bounded_cloudinary_chunks(
        self,
        upload_large,
        upload,
    ):
        upload_large.return_value = {"public_id": "post-media/video"}
        content = SimpleUploadedFile(
            "video.mp4",
            b"video-bytes",
            content_type="video/mp4",
        )

        response = PostMediaCloudinaryStorage()._upload(
            "__video__/video.mp4",
            content,
        )

        self.assertEqual(response["public_id"], "post-media/video")
        upload_large.assert_called_once()
        self.assertEqual(
            upload_large.call_args.kwargs["chunk_size"],
            8 * 1024 * 1024,
        )
        self.assertEqual(
            upload_large.call_args.kwargs["resource_type"],
            "video",
        )
        upload.assert_not_called()

    @patch("apps.posts.storage.uploader.upload")
    @patch("apps.posts.storage.uploader.upload_large")
    def test_image_fallback_upload_keeps_standard_cloudinary_upload(
        self,
        upload_large,
        upload,
    ):
        upload.return_value = {"public_id": "post-media/image"}
        content = SimpleUploadedFile(
            "image.jpg",
            b"image-bytes",
            content_type="image/jpeg",
        )

        response = PostMediaCloudinaryStorage()._upload(
            "__image__/image.jpg",
            content,
        )

        self.assertEqual(response["public_id"], "post-media/image")
        upload.assert_called_once()
        self.assertEqual(
            upload.call_args.kwargs["resource_type"],
            "image",
        )
        upload_large.assert_not_called()

    @patch("apps.posts.storage.requests.get")
    def test_open_streams_cloudinary_response_without_buffering(self, get):
        raw = SimpleNamespace(
            decode_content=False,
            read=BytesIO(b"streamed-video").read,
            close=Mock(),
        )
        response = Mock(
            status_code=200,
            headers={"Content-Length": "14"},
            raw=raw,
        )
        get.return_value = response
        storage = PostMediaCloudinaryStorage()
        storage._get_url = lambda name: "https://media.example/video.mp4"

        media_file = storage._open("video.mp4")

        self.assertEqual(media_file.size, 14)
        self.assertEqual(media_file.read(8), b"streamed")
        self.assertEqual(media_file.tell(), 8)
        get.assert_called_once_with(
            "https://media.example/video.mp4",
            stream=True,
            timeout=(10, 120),
        )

        media_file.close()
        response.close.assert_called_once_with()

    @patch("apps.posts.storage.requests.head")
    def test_size_uses_bounded_cloudinary_request(self, head):
        head.return_value = Mock(
            status_code=200,
            headers={"content-length": "42"},
        )
        storage = PostMediaCloudinaryStorage()
        storage._get_url = lambda name: "https://media.example/video.mp4"

        self.assertEqual(storage.size("video.mp4"), 42)
        head.assert_called_once_with(
            "https://media.example/video.mp4",
            timeout=(10, 120),
        )


class FacebookStoryPublisherTests(SimpleTestCase):
    @patch("apps.posts.publishing.meta.MetaCredentialService.get_access_token")
    @patch("apps.posts.publishing.meta.MetaAPIClient")
    @patch.object(MetaPublisher, "_media")
    def test_video_story_upload_uses_underlying_stream(self, media, client_class, get_token):
        underlying_stream = Mock()
        file_proxy = SimpleNamespace(
            url="https://media.example/video.mp4",
            file=underlying_stream,
            open=Mock(),
            close=Mock(),
        )
        story_media = SimpleNamespace(
            media_type="VIDEO",
            file=file_proxy,
            file_size=14,
            duration=5,
        )
        target = SimpleNamespace(
            id="target-1",
            content_type="STORY",
            social_account=SimpleNamespace(
                platform="facebook",
                platform_account_id="page-1",
            ),
            post=SimpleNamespace(caption=""),
        )
        media.return_value = [story_media]
        get_token.return_value = "token"
        client_class.return_value.post.side_effect = [
            {
                "video_id": "video-1",
                "upload_url": "https://upload.example/video-1",
            },
            {"id": "story-1"},
        ]

        result = MetaPublisher().publish_facebook(post_platform=target)

        self.assertEqual(result["external_post_id"], "story-1")
        upload_call = client_class.return_value.upload_reel_video.call_args
        self.assertIs(upload_call.kwargs["video_file"], underlying_stream)
        self.assertEqual(upload_call.kwargs["file_size"], 14)
        file_proxy.open.assert_called_once_with("rb")
        file_proxy.close.assert_called_once_with()


class DirectMediaUploadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="media-owner@example.com",
            password="password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-DIRECT-MEDIA",
            name="Direct Media",
            slug="direct-media",
            industry="Retail",
            created_by=self.user,
        )
        self.account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id="page-direct-media",
            account_name="Page",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @override_settings(
        MEDIA_UPLOAD_MAX_IMAGE_BYTES=10_000_000,
        MEDIA_UPLOAD_MAX_VIDEO_BYTES=100_000_000,
    )
    @patch("apps.posts.views._media_upload_response")
    def test_oversized_upload_session_is_rejected_before_signing(
        self,
        upload_response,
    ):
        for content_type, filename, size in (
            ("image/png", "image.png", 10_000_001),
            ("video/mp4", "video.mp4", 100_000_001),
        ):
            with self.subTest(content_type=content_type):
                response = self.client.post(
                    "/api/posts/organizations/ORG-DIRECT-MEDIA/media-upload-sessions/",
                    {"filename": filename, "content_type": content_type, "size": size},
                    format="json",
                )
                self.assertEqual(response.status_code, 400)
        upload_response.assert_not_called()
        self.assertFalse(
            MediaUploadSession.objects.filter(organization=self.organization).exists()
        )

    @override_settings(MEDIA_UPLOAD_MAX_VIDEO_BYTES=100_000_000)
    @patch("apps.posts.views.cloudinary_api.resource")
    def test_finalize_rejects_asset_above_current_size_cap(self, resource):
        session = MediaUploadSession.objects.create(
            organization=self.organization,
            created_by=self.user,
            original_filename="legacy-large.mp4",
            content_type="video/mp4",
            media_type=PostMediaType.VIDEO,
            expected_size=100_000_001,
            cloudinary_public_id="post-media/org/legacy-large",
            cloudinary_resource_type="video",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        resource.return_value = {
            "public_id": session.cloudinary_public_id,
            "resource_type": "video",
            "asset_id": "asset-large",
            "secure_url": "https://res.cloudinary.com/example/video/upload/large.mp4",
            "version": 1,
            "bytes": 100_000_001,
            "format": "mp4",
            "width": 1080,
            "height": 1920,
            "duration": 20,
        }

        response = self.client.post(
            f"/api/posts/organizations/ORG-DIRECT-MEDIA/media-upload-sessions/{session.id}/",
            {
                "public_id": session.cloudinary_public_id,
                "resource_type": "video",
                "asset_id": "asset-large",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        session.refresh_from_db()
        self.assertEqual(session.status, MediaUploadStatus.FAILED)
        self.assertIn("current media upload limit", session.error_message)

    @override_settings(MEDIA_UPLOAD_MAX_VIDEO_BYTES=100_000_000)
    @patch("apps.posts.views.cloudinary_api.resource")
    def test_finalize_rejects_declared_and_actual_size_mismatch(self, resource):
        session = MediaUploadSession.objects.create(
            organization=self.organization,
            created_by=self.user,
            original_filename="video.mp4",
            content_type="video/mp4",
            media_type=PostMediaType.VIDEO,
            expected_size=1_000,
            cloudinary_public_id="post-media/org/mismatch",
            cloudinary_resource_type="video",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        resource.return_value = {
            "public_id": session.cloudinary_public_id,
            "resource_type": "video",
            "asset_id": "asset-mismatch",
            "secure_url": "https://res.cloudinary.com/example/video/upload/video.mp4",
            "version": 1,
            "bytes": 1_001,
            "format": "mp4",
            "width": 1080,
            "height": 1920,
            "duration": 20,
        }

        response = self.client.post(
            f"/api/posts/organizations/ORG-DIRECT-MEDIA/media-upload-sessions/{session.id}/",
            {
                "public_id": session.cloudinary_public_id,
                "resource_type": "video",
                "asset_id": "asset-mismatch",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        session.refresh_from_db()
        self.assertEqual(session.status, MediaUploadStatus.FAILED)
        self.assertIn("size does not match", session.error_message)

    @patch(
        "apps.posts.views._media_upload_response",
        return_value={"session_id": "session", "media_asset_id": "session"},
    )
    def test_create_session_is_organization_scoped(self, _response):
        response = self.client.post(
            "/api/posts/organizations/ORG-DIRECT-MEDIA/media-upload-sessions/",
            {
                "filename": "video.mp4",
                "content_type": "video/mp4",
                "size": 25 * 1024 * 1024,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        session = MediaUploadSession.objects.get(
            organization=self.organization,
            created_by=self.user,
        )
        self.assertEqual(session.status, MediaUploadStatus.CREATED)
        self.assertEqual(session.expected_size, 25 * 1024 * 1024)

    @patch("apps.posts.views.cloudinary_utils.api_sign_request", return_value="signature")
    def test_signed_upload_disables_overwrite(self, sign_request):
        response = self.client.post(
            "/api/posts/organizations/ORG-DIRECT-MEDIA/media-upload-sessions/",
            {
                "filename": "video.mp4",
                "content_type": "video/mp4",
                "size": 1024,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(sign_request.call_args.args[0]["overwrite"], "false")
        self.assertEqual(response.data["data"]["overwrite"], "false")

    @patch("apps.posts.views.cloudinary_api.resource")
    @patch("apps.posts.views._media_upload_response")
    def test_finalize_verifies_cloudinary_metadata_and_is_idempotent(
        self,
        upload_response,
        resource,
    ):
        upload_response.return_value = {
            "session_id": "placeholder",
            "media_asset_id": "placeholder",
        }
        self.client.post(
            "/api/posts/organizations/ORG-DIRECT-MEDIA/media-upload-sessions/",
            {
                "filename": "video.mp4",
                "content_type": "video/mp4",
                "size": 1024,
            },
            format="json",
        )
        session = MediaUploadSession.objects.latest("created_at")
        upload_response.return_value = {
            "session_id": str(session.id),
            "media_asset_id": str(session.id),
        }
        resource.return_value = {
            "public_id": session.cloudinary_public_id,
            "resource_type": "video",
            "asset_id": "asset-1",
            "secure_url": "https://res.cloudinary.com/example/video/upload/video.mp4",
            "version": 7,
            "bytes": 1024,
            "width": 1080,
            "height": 1920,
            "duration": 10,
            "frame_rate": 30,
            "video_codec": "h264",
            "audio_codec": "aac",
        }
        payload = {
            "public_id": session.cloudinary_public_id,
            "resource_type": "video",
            "asset_id": "asset-1",
        }
        response = self.client.post(
            f"/api/posts/organizations/ORG-DIRECT-MEDIA/media-upload-sessions/{session.id}/",
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        session.refresh_from_db()
        self.assertEqual(session.status, MediaUploadStatus.READY)
        self.assertEqual(session.bytes_uploaded, 1024)
        self.assertEqual(session.cloudinary_version, 7)
        self.assertIn("::v7", session.storage_name)
        self.assertEqual(resource.call_args.args[0], session.cloudinary_public_id)
        self.assertEqual(resource.call_args.kwargs["resource_type"], "video")
        self.assertEqual(resource.call_args.kwargs["type"], "upload")
        self.assertTrue(resource.call_args.kwargs["media_metadata"])

        repeated = self.client.post(
            f"/api/posts/organizations/ORG-DIRECT-MEDIA/media-upload-sessions/{session.id}/",
            payload,
            format="json",
        )
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(resource.call_count, 1)

    def test_idempotent_post_creation_does_not_duplicate_posts(self):
        session = MediaUploadSession.objects.create(
            organization=self.organization,
            created_by=self.user,
            original_filename="video.mp4",
            content_type="video/mp4",
            media_type="VIDEO",
            expected_size=1024,
            bytes_uploaded=1024,
            cloudinary_public_id="post-media/org/video",
            cloudinary_resource_type="video",
            status=MediaUploadStatus.READY,
            metadata={"width": 1080, "height": 1920, "duration": 10, "frame_rate": 30},
            expires_at=timezone.now() + timedelta(hours=1),
        )
        first = create_post(
            organization=self.organization,
            created_by=self.user,
            idempotency_key="request-key",
            validated_data={
                "targets": [{"social_account": self.account.id, "content_type": "POST"}],
                "media_asset_ids": [str(session.id)],
                "caption": "hello",
                "publish_type": "DRAFT",
                "timezone": "UTC",
            },
        )
        second = create_post(
            organization=self.organization,
            created_by=self.user,
            idempotency_key="request-key",
            validated_data={
                "targets": [{"social_account": self.account.id, "content_type": "POST"}],
                "media_asset_ids": [str(session.id)],
                "caption": "changed",
                "publish_type": "DRAFT",
                "timezone": "UTC",
            },
        )
        self.assertEqual(first.id, second.id)
        self.assertEqual(Post.objects.filter(organization=self.organization).count(), 1)

    def test_upload_session_requires_organization_owner(self):
        other_user = User.objects.create_user(
            email="other-owner@example.com",
            password="password",
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.post(
            "/api/posts/organizations/ORG-DIRECT-MEDIA/media-upload-sessions/",
            {
                "filename": "video.mp4",
                "content_type": "video/mp4",
                "size": 1024,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_created_by_none_organization_rejects_authenticated_user(self):
        unowned = Organization.objects.create(
            organization_id="ORG-NO-OWNER",
            name="No Owner",
            slug="no-owner",
            industry="Retail",
            created_by=None,
        )
        response = self.client.post(
            f"/api/posts/organizations/{unowned.organization_id}/media-upload-sessions/",
            {
                "filename": "video.mp4",
                "content_type": "video/mp4",
                "size": 1024,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_cross_organization_upload_session_access_is_rejected(self):
        other_user = User.objects.create_user(
            email="other-org-owner@example.com",
            password="password",
        )
        other_org = Organization.objects.create(
            organization_id="ORG-OTHER-MEDIA",
            name="Other Media",
            slug="other-media",
            industry="Retail",
            created_by=other_user,
        )
        session = MediaUploadSession.objects.create(
            organization=other_org,
            created_by=other_user,
            original_filename="video.mp4",
            content_type="video/mp4",
            media_type="VIDEO",
            expected_size=1024,
            cloudinary_public_id="post-media/other/video",
            cloudinary_resource_type="video",
            status=MediaUploadStatus.CREATED,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        response = self.client.get(
            f"/api/posts/organizations/{other_org.organization_id}/media-upload-sessions/{session.id}/",
        )
        self.assertEqual(response.status_code, 403)

    @patch(
        "apps.posts.views._media_upload_response",
        return_value={"session_id": "owner-session", "signature": "signature"},
    )
    def test_owner_can_read_unexpired_session_and_receive_signature(self, upload_response):
        session = MediaUploadSession.objects.create(
            organization=self.organization,
            created_by=self.user,
            original_filename="video.mp4",
            content_type="video/mp4",
            media_type="VIDEO",
            expected_size=1024,
            cloudinary_public_id="post-media/org/owner",
            cloudinary_resource_type="video",
            status=MediaUploadStatus.UPLOADING,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        response = self.client.get(
            f"/api/posts/organizations/{self.organization.organization_id}/media-upload-sessions/{session.id}/",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["upload"]["signature"], "signature")
        upload_response.assert_called_once_with(session)

    def test_unauthorized_user_cannot_access_post_detail_or_media(self):
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            caption="Owner post",
            publish_type="DRAFT",
            status="DRAFT",
        )
        other_user = User.objects.create_user(
            email="post-unauthorized@example.com",
            password="password",
        )
        self.client.force_authenticate(user=other_user)

        detail = self.client.get(
            f"/api/posts/organizations/{self.organization.organization_id}/{post.id}/",
        )
        self.assertEqual(detail.status_code, 403)

        media = self.client.post(
            f"/api/posts/organizations/{self.organization.organization_id}/{post.id}/media/",
            {
                "file": SimpleUploadedFile("image.png", b"not-an-image", content_type="image/png"),
                "media_type": "IMAGE",
            },
            format="multipart",
        )
        self.assertEqual(media.status_code, 403)

    def test_unauthorized_user_cannot_create_post_with_foreign_media_asset(self):
        session = MediaUploadSession.objects.create(
            organization=self.organization,
            created_by=self.user,
            original_filename="video.mp4",
            content_type="video/mp4",
            media_type="VIDEO",
            expected_size=1024,
            cloudinary_public_id="post-media/org/foreign",
            cloudinary_resource_type="video",
            status=MediaUploadStatus.READY,
            cloudinary_asset_id="asset-foreign",
            cloudinary_version=5,
            metadata={"width": 1080, "height": 1920, "duration": 10, "frame_rate": 30},
            expires_at=timezone.now() + timedelta(hours=1),
        )
        other_user = User.objects.create_user(
            email="foreign-media-user@example.com",
            password="password",
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.post(
            f"/api/posts/organizations/{self.organization.organization_id}/",
            {
                "targets": [],
                "media_asset_ids": [str(session.id)],
                "caption": "forbidden",
                "publish_type": "DRAFT",
                "timezone": "UTC",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_expired_ready_session_cannot_be_attached(self):
        session = MediaUploadSession.objects.create(
            organization=self.organization,
            created_by=self.user,
            original_filename="video.mp4",
            content_type="video/mp4",
            media_type="VIDEO",
            expected_size=1024,
            bytes_uploaded=1024,
            cloudinary_public_id="post-media/org/expired",
            cloudinary_resource_type="video",
            cloudinary_asset_id="asset-expired",
            cloudinary_version=3,
            status=MediaUploadStatus.READY,
            metadata={"width": 1080, "height": 1920, "duration": 10, "frame_rate": 30},
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        with self.assertRaises(MediaUploadValidationError):
            create_post(
                organization=self.organization,
                created_by=self.user,
                idempotency_key="expired-session-key",
                validated_data={
                    "targets": [{"social_account": self.account.id, "content_type": "POST"}],
                    "media_asset_ids": [str(session.id)],
                    "caption": "expired",
                    "publish_type": "DRAFT",
                    "timezone": "UTC",
                },
            )

    def test_already_attached_media_reference_returns_bad_request(self):
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            caption="Existing post",
            publish_type="DRAFT",
            status="DRAFT",
        )
        session = MediaUploadSession.objects.create(
            organization=self.organization,
            created_by=self.user,
            original_filename="video.mp4",
            content_type="video/mp4",
            media_type="VIDEO",
            expected_size=1024,
            bytes_uploaded=1024,
            cloudinary_public_id="post-media/org/already-attached",
            cloudinary_resource_type="video",
            status=MediaUploadStatus.READY,
            attached_post=post,
            metadata={"width": 1080, "height": 1920, "duration": 10, "frame_rate": 30},
            expires_at=timezone.now() + timedelta(hours=1),
        )
        response = self.client.post(
            f"/api/posts/organizations/{self.organization.organization_id}/",
            {
                "targets": [
                    {
                        "social_account": str(self.account.id),
                        "content_type": "POST",
                    }
                ],
                "media_asset_ids": [str(session.id)],
                "caption": "stale media",
                "publish_type": "DRAFT",
                "timezone": "UTC",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("unavailable or not ready", str(response.data))

    def test_expired_session_get_does_not_return_signature(self):
        session = MediaUploadSession.objects.create(
            organization=self.organization,
            created_by=self.user,
            original_filename="video.mp4",
            content_type="video/mp4",
            media_type="VIDEO",
            expected_size=1024,
            cloudinary_public_id="post-media/org/expired-get",
            cloudinary_resource_type="video",
            status=MediaUploadStatus.UPLOADING,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        with patch("apps.posts.views._media_upload_response") as upload_response:
            response = self.client.get(
                f"/api/posts/organizations/{self.organization.organization_id}/media-upload-sessions/{session.id}/",
            )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("upload", response.data["data"])
        upload_response.assert_not_called()
        session.refresh_from_db()
        self.assertEqual(session.status, MediaUploadStatus.EXPIRED)

    @patch("apps.posts.tasks.cloudinary_uploader.destroy", side_effect=RuntimeError("network"))
    def test_cleanup_failure_keeps_session_retryable(self, _destroy):
        session = MediaUploadSession.objects.create(
            organization=self.organization,
            created_by=self.user,
            original_filename="video.mp4",
            content_type="video/mp4",
            media_type="VIDEO",
            expected_size=1024,
            cloudinary_public_id="post-media/org/cleanup",
            cloudinary_resource_type="video",
            status=MediaUploadStatus.READY,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        cleanup_expired_media_upload_sessions_task()
        session.refresh_from_db()
        self.assertEqual(session.status, MediaUploadStatus.READY)


class InstagramImageValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="instagram-image-owner@example.com",
            password="password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-INSTAGRAM-IMAGE",
            name="Instagram Image Validation",
            slug="instagram-image-validation",
            industry="Retail",
            created_by=self.user,
        )
        self.instagram = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="instagram-image-validation",
            account_name="Instagram",
        )
        self.facebook = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id="facebook-image-validation",
            account_name="Facebook",
        )

    def make_session(self, *, width, height, image_format="jpeg"):
        return MediaUploadSession.objects.create(
            organization=self.organization,
            created_by=self.user,
            original_filename="image.jpg",
            content_type="image/jpeg",
            media_type=PostMediaType.IMAGE,
            expected_size=100,
            bytes_uploaded=100,
            cloudinary_public_id="post-media/instagram-image",
            cloudinary_resource_type="image",
            status=MediaUploadStatus.READY,
            metadata={
                "width": width,
                "height": height,
                "format": image_format,
            },
            expires_at=timezone.now() + timedelta(hours=1),
        )

    def validate(self, session, targets=None):
        validate_media_assets_for_targets(
            organization=self.organization,
            created_by=self.user,
            media_asset_ids=[str(session.id)],
            targets=targets or [
                {"social_account": self.instagram.id, "content_type": "POST"},
            ],
        )

    def test_landscape_ratio_above_limit_is_rejected(self):
        session = self.make_session(width=683, height=228)

        with self.assertRaisesRegex(MediaUploadValidationError, "683x228.*2.99"):
            self.validate(session)

    def test_portrait_ratio_below_limit_is_rejected(self):
        session = self.make_session(width=355, height=532)

        with self.assertRaisesRegex(MediaUploadValidationError, "355x532.*0.67"):
            self.validate(session)

    def test_boundary_ratios_are_accepted(self):
        for width, height in ((3, 4), (4, 5), (191, 100), (1085, 1447)):
            with self.subTest(width=width, height=height):
                session = self.make_session(width=width, height=height)
                self.validate(session)

    def test_ratio_below_new_minimum_is_rejected(self):
        session = self.make_session(width=7497, height=10000)

        with self.assertRaisesRegex(MediaUploadValidationError, "7497x10000.*0.75"):
            self.validate(session)

    def test_facebook_only_target_ignores_instagram_image_constraints(self):
        session = self.make_session(width=683, height=228, image_format="png")

        self.validate(
            session,
            targets=[
                {"social_account": self.facebook.id, "content_type": "POST"},
            ],
        )

    def test_valid_image_for_instagram_and_facebook_preserves_multi_target_validation(self):
        session = self.make_session(width=1080, height=1080)

        self.validate(
            session,
            targets=[
                {"social_account": self.instagram.id, "content_type": "POST"},
                {"social_account": self.facebook.id, "content_type": "POST"},
            ],
        )

    def test_png_format_is_accepted_for_instagram(self):
        session = self.make_session(
            width=1080,
            height=1080,
            image_format="png",
        )

        self.validate(session)

    def test_png_image_remains_accepted_for_instagram_story(self):
        session = self.make_session(
            width=1080,
            height=1080,
            image_format="png",
        )

        self.validate(
            session,
            targets=[
                {"social_account": self.instagram.id, "content_type": "STORY"},
            ],
        )

    def test_single_tall_png_can_be_saved_for_instagram_story(self):
        session = self.make_session(
            width=1080,
            height=1920,
            image_format="png",
        )
        post = create_post(
            organization=self.organization,
            created_by=self.user,
            validated_data={
                "targets": [{
                    "social_account": self.instagram.id,
                    "content_type": "STORY",
                }],
                "media_asset_ids": [str(session.id)],
                "caption": "Story draft",
                "publish_type": PostPublishType.DRAFT,
                "timezone": "UTC",
            },
        )

        self.assertEqual(post.platforms.get().content_type, "STORY")
        self.assertEqual(post.media.get().original_filename, "image.jpg")

    def test_instagram_story_rejects_more_than_one_media_item(self):
        sessions = [
            self.make_session(width=1080, height=1920, image_format="png"),
            self.make_session(width=1200, height=1500, image_format="png"),
        ]

        with self.assertRaisesRegex(MediaUploadValidationError, "exactly one"):
            create_post(
                organization=self.organization,
                created_by=self.user,
                validated_data={
                    "targets": [{
                        "social_account": self.instagram.id,
                        "content_type": "STORY",
                    }],
                    "media_asset_ids": [str(session.id) for session in sessions],
                    "caption": "Story draft",
                    "publish_type": PostPublishType.DRAFT,
                    "timezone": "UTC",
                },
            )
        self.assertFalse(Post.objects.filter(organization=self.organization).exists())

    def test_png_format_is_accepted_for_instagram_carousel(self):
        session = self.make_session(
            width=1080,
            height=1080,
            image_format="png",
        )

        self.validate(
            session,
            targets=[
                {"social_account": self.instagram.id, "content_type": "CAROUSEL"},
            ],
        )

    def test_webp_format_remains_rejected_for_instagram(self):
        session = self.make_session(
            width=1080,
            height=1080,
            image_format="webp",
        )

        with self.assertRaisesRegex(MediaUploadValidationError, "WEBP.*JPEG or PNG"):
            self.validate(session)

    def test_missing_image_metadata_is_rejected_explicitly(self):
        session = self.make_session(width=4, height=5)
        session.metadata = {}
        session.save(update_fields=["metadata"])

        with self.assertRaisesRegex(MediaUploadValidationError, "dimensions could not be verified"):
            self.validate(session)

    def test_legacy_multipart_image_is_validated_for_instagram(self):
        buffer = BytesIO()
        Image.new("RGB", (683, 228)).save(buffer, format="JPEG")
        image = SimpleUploadedFile(
            "wide.jpg",
            buffer.getvalue(),
            content_type="image/jpeg",
        )

        with self.assertRaisesRegex(MediaUploadValidationError, "683x228.*2.99"):
            create_post(
                organization=self.organization,
                created_by=self.user,
                validated_data={
                    "targets": [
                        {"social_account": self.instagram.id, "content_type": "POST"},
                    ],
                    "media": [{"file": image, "media_type": PostMediaType.IMAGE}],
                    "caption": "invalid image",
                    "publish_type": PostPublishType.DRAFT,
                    "timezone": "UTC",
                },
            )

    def test_legacy_multipart_png_image_is_accepted_for_instagram(self):
        buffer = BytesIO()
        Image.new("RGB", (1080, 1080)).save(buffer, format="PNG")
        image = SimpleUploadedFile(
            "square.png",
            buffer.getvalue(),
            content_type="image/png",
        )

        validate_multipart_media_for_targets(
            media_items=[{"file": image, "media_type": PostMediaType.IMAGE}],
            targets=[
                {"social_account": self.instagram.id, "content_type": "POST"},
            ],
            organization=self.organization,
        )
