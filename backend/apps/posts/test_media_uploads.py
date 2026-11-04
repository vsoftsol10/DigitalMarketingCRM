from unittest.mock import patch
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.social_accounts.models import SocialAccount, SocialPlatform

from .models import MediaUploadSession, MediaUploadStatus, Post
from .tasks import cleanup_expired_media_upload_sessions_task
from .services import create_post


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
        with self.assertRaises(ValueError):
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
