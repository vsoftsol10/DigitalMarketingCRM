from datetime import timedelta
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from PIL import Image

from apps.accounts.models import User
from apps.integrations.instagram.exceptions import InstagramAPIError
from apps.organizations.models import Organization
from apps.social_accounts.models import SocialAccount, SocialPlatform

from .models import Post, PostMedia, PostPlatform, PostPublishType, PostStatus
from .publishing.exceptions import MediaProcessingPending, PublishingValidationError
from .publishing.meta import MetaPublisher
from .serializers import PostCreateSerializer
from .services import create_post, validate_target_accounts
from .tasks import publish_post_task


def image_file():
    buffer = BytesIO()
    Image.new("RGB", (20, 20)).save(buffer, format="JPEG")
    return SimpleUploadedFile("post.jpg", buffer.getvalue(), content_type="image/jpeg")


class PostCreationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", first_name="Owner", password="password")
        self.organization = Organization.objects.create(
            organization_id="ORG-POST-1", name="Post Organization", slug="post-organization",
            industry="Retail", created_by=self.user,
        )
        self.account = SocialAccount.objects.create(
            organization=self.organization, platform=SocialPlatform.FACEBOOK,
            platform_account_id="page-1", account_name="Page",
        )

    def test_draft_persists_without_consuming_provider_credentials(self):
        post = create_post(
            organization=self.organization, created_by=self.user,
            validated_data={
                "targets": [{"social_account": self.account.id, "content_type": "POST"}],
                "media": [{"file": image_file(), "media_type": "IMAGE"}],
                "caption": "Draft", "publish_type": PostPublishType.DRAFT, "timezone": "Asia/Kolkata",
            },
        )
        self.assertEqual(post.status, PostStatus.DRAFT)
        self.assertEqual(post.platforms.count(), 1)
        self.assertEqual(post.media.count(), 1)

    def test_target_from_another_organization_is_rejected(self):
        other = Organization.objects.create(organization_id="ORG-POST-2", name="Other", slug="other", industry="Retail")
        other_account = SocialAccount.objects.create(
            organization=other, platform=SocialPlatform.FACEBOOK,
            platform_account_id="page-2", account_name="Other Page",
        )
        with self.assertRaises(ValueError):
            validate_target_accounts(
                organization=self.organization,
                targets=[{"social_account": other_account.id}],
                require_publishable=False,
            )

    def test_past_schedule_is_invalid(self):
        local = timezone.localtime(timezone.now()) - timedelta(minutes=5)
        serializer = PostCreateSerializer(data={
            "targets": [{"social_account": self.account.id, "content_type": "POST"}],
            "publish_type": PostPublishType.SCHEDULE,
            "publish_date": local.date(), "publish_time": local.time(), "timezone": "Asia/Kolkata",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("publish_time", serializer.errors)

    def test_invalid_video_content_type_is_rejected(self):
        invalid_video = SimpleUploadedFile("bad.mov", b"not-video", content_type="video/quicktime")
        serializer = PostCreateSerializer(data={
            "targets": [{"social_account": self.account.id}], "publish_type": PostPublishType.DRAFT,
            "media": [{"file": invalid_video, "media_type": "VIDEO"}],
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("media", serializer.errors)

    @patch("apps.posts.publishing.meta.InstagramAPIClient")
    @patch("apps.posts.publishing.meta.decrypt_instagram_token")
    @patch("apps.posts.publishing.meta.get_active_instagram_credential")
    def test_instagram_image_publish_uses_image_container_contract(
        self,
        get_credential,
        decrypt_token,
        client_class,
    ):
        account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="instagram-user-1",
            account_name="Instagram",
        )
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            caption="Image post",
            publish_type=PostPublishType.NOW,
            status=PostStatus.PUBLISHING,
        )
        target = PostPlatform.objects.create(
            post=post,
            platform=SocialPlatform.INSTAGRAM,
            social_account=account,
            content_type="POST",
        )
        client = client_class.return_value
        client.graph_post.side_effect = [{"id": "container-1"}, {"id": "post-1"}]
        client.graph_get.return_value = {"status_code": "FINISHED"}
        get_credential.return_value = SimpleNamespace(
            encrypted_access_token="encrypted-token",
        )
        decrypt_token.return_value = "access-token"

        with patch.object(
            MetaPublisher,
            "_media",
            return_value=[
                SimpleNamespace(
                    media_type="IMAGE",
                    file=SimpleNamespace(url="https://media.example/post.jpg"),
                )
            ],
        ):
            MetaPublisher().publish_instagram(post_platform=target)

        self.assertEqual(
            client.graph_post.call_args_list[0].kwargs["data"],
            {
                "image_url": "https://media.example/post.jpg",
                "caption": "Image post",
            },
        )

    @patch("apps.posts.publishing.meta.MetaCredentialService.get_access_token")
    @patch("apps.posts.publishing.meta.MetaAPIClient")
    def test_facebook_reel_uses_reels_endpoint(self, client_class, get_token):
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            publish_type=PostPublishType.NOW,
            status=PostStatus.PUBLISHING,
        )
        target = PostPlatform.objects.create(
            post=post,
            platform=SocialPlatform.FACEBOOK,
            social_account=self.account,
            content_type="REEL",
        )
        get_token.return_value = "access-token"
        client_class.return_value.post.side_effect = [
            {"video_id": "reel-1", "upload_url": "https://upload.example/reel"},
            {"id": "reel-1"},
        ]

        with patch.object(
            MetaPublisher,
            "_media",
            return_value=[
                SimpleNamespace(
                    media_type="VIDEO",
                    file=SimpleNamespace(
                        url="https://media.example/reel.mp4",
                        size=100,
                        open=lambda mode: None,
                        close=lambda: None,
                    ),
                    file_size=100,
                )
            ],
        ):
            MetaPublisher().publish_facebook(post_platform=target)

        self.assertEqual(
            client_class.return_value.post.call_args_list[0].args[0],
            "/page-1/video_reels",
        )
        self.assertEqual(
            client_class.return_value.post.call_args_list[1].kwargs["data"]["upload_phase"],
            "FINISH",
        )

    @patch("apps.posts.publishing.meta.InstagramAPIClient")
    @patch("apps.posts.publishing.meta.decrypt_instagram_token")
    @patch("apps.posts.publishing.meta.get_active_instagram_credential")
    def test_instagram_carousel_persists_child_containers_before_retry(
        self,
        get_credential,
        decrypt_token,
        client_class,
    ):
        account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="instagram-user-carousel",
            account_name="Instagram",
        )
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            publish_type=PostPublishType.NOW,
            status=PostStatus.PUBLISHING,
        )
        target = PostPlatform.objects.create(
            post=post,
            platform=SocialPlatform.INSTAGRAM,
            social_account=account,
            content_type="POST",
        )
        client_class.return_value.graph_post.side_effect = [
            {"id": "child-1"},
            {"id": "child-2"},
        ]
        get_credential.return_value = SimpleNamespace(
            encrypted_access_token="encrypted-token",
        )
        decrypt_token.return_value = "access-token"

        with patch.object(
            MetaPublisher,
            "_media",
            return_value=[
                SimpleNamespace(
                    media_type="IMAGE",
                    mime_type="image/jpeg",
                    file=SimpleNamespace(
                        url="https://res.cloudinary.com/example/image/upload/posts/2026/one"
                    ),
                ),
                SimpleNamespace(
                    media_type="IMAGE",
                    mime_type="image/jpeg",
                    file=SimpleNamespace(
                        url="https://res.cloudinary.com/example/image/upload/posts/2026/two"
                    ),
                ),
            ],
        ):
            with self.assertRaises(MediaProcessingPending):
                MetaPublisher().publish_instagram(post_platform=target)

        target.refresh_from_db()
        self.assertEqual(target.provider_state["carousel_children"], ["child-1", "child-2"])
        self.assertEqual(
            client_class.return_value.graph_post.call_args_list[0].kwargs["data"]["image_url"],
            "https://res.cloudinary.com/example/image/upload/posts/2026/one.jpg",
        )
        self.assertEqual(
            client_class.return_value.graph_post.call_args_list[1].kwargs["data"]["image_url"],
            "https://res.cloudinary.com/example/image/upload/posts/2026/two.jpg",
        )

    @patch("apps.posts.publishing.meta.InstagramAPIClient")
    @patch("apps.posts.publishing.meta.decrypt_instagram_token")
    @patch("apps.posts.publishing.meta.get_active_instagram_credential")
    def test_instagram_carousel_retries_transient_image_delivery_rejection(
        self,
        get_credential,
        decrypt_token,
        client_class,
    ):
        account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="instagram-carousel-retry",
            account_name="Instagram",
        )
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            publish_type=PostPublishType.NOW,
            status=PostStatus.PUBLISHING,
        )
        target = PostPlatform.objects.create(
            post=post,
            platform=SocialPlatform.INSTAGRAM,
            social_account=account,
            content_type="POST",
        )
        get_credential.return_value = SimpleNamespace(
            encrypted_access_token="encrypted-token",
        )
        decrypt_token.return_value = "access-token"
        client_class.return_value.graph_post.side_effect = InstagramAPIError(
            "Instagram rejected the source image.",
            error_payload={"error": {"code": 9004}},
        )

        with patch.object(
            MetaPublisher,
            "_media",
            return_value=[
                SimpleNamespace(
                    media_type="IMAGE",
                    mime_type="image/jpeg",
                    file=SimpleNamespace(
                        url="https://res.cloudinary.com/example/image/upload/posts/2026/photo"
                    ),
                ),
                SimpleNamespace(
                    media_type="IMAGE",
                    mime_type="image/jpeg",
                    file=SimpleNamespace(
                        url="https://res.cloudinary.com/example/image/upload/posts/2026/photo-two"
                    ),
                ),
            ],
        ):
            with self.assertRaises(MediaProcessingPending):
                MetaPublisher().publish_instagram(post_platform=target)

        self.assertEqual(
            client_class.return_value.graph_post.call_args.kwargs["data"]["image_url"],
            "https://res.cloudinary.com/example/image/upload/posts/2026/photo.jpg",
        )

    def test_post_media_storage_uses_cloudinary_video_resource_type_for_mp4(self):
        storage = PostMedia._meta.get_field("file").storage

        self.assertEqual(storage._get_resource_type("posts/reel.mp4"), "video")
        self.assertEqual(storage._get_resource_type("posts/image.jpg"), "image")
        self.assertEqual(
            storage._get_resource_type("__video__/posts/reel"),
            "video",
        )

    def test_provider_execution_state_is_scoped_to_one_target(self):
        instagram_account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="instagram-state-isolation",
            account_name="Instagram",
        )
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            publish_type=PostPublishType.NOW,
            status=PostStatus.PUBLISHING,
        )
        facebook_target = PostPlatform.objects.create(
            post=post,
            platform=SocialPlatform.FACEBOOK,
            social_account=self.account,
            content_type="POST",
        )
        instagram_target = PostPlatform.objects.create(
            post=post,
            platform=SocialPlatform.INSTAGRAM,
            social_account=instagram_account,
            content_type="POST",
            provider_state={"carousel_children": ["child-1", "child-2"]},
            provider_container_id="instagram-container",
        )

        facebook_target.refresh_from_db()
        instagram_target.refresh_from_db()

        self.assertEqual(facebook_target.provider_state, {})
        self.assertEqual(facebook_target.provider_container_id, "")
        self.assertEqual(
            instagram_target.provider_state,
            {"carousel_children": ["child-1", "child-2"]},
        )

    @patch("apps.posts.storage.uploader.upload")
    def test_post_media_storage_retains_video_resource_type_after_upload(
        self,
        upload,
    ):
        storage = PostMedia._meta.get_field("file").storage
        upload.return_value = {"public_id": "posts/2026/reel"}

        saved_name = storage._save("posts/2026/reel.mp4", BytesIO(b"video"))

        self.assertEqual(saved_name, "__video__/posts/2026/reel")
        self.assertEqual(storage._get_resource_type(saved_name), "video")
        self.assertEqual(upload.call_args.kwargs["resource_type"], "video")

    @patch("apps.posts.storage.uploader.upload")
    def test_post_media_storage_uploads_mp4_as_cloudinary_video(self, upload):
        storage = PostMedia._meta.get_field("file").storage

        storage._upload(
            "posts/2026/reel.mp4",
            BytesIO(b"video"),
        )

        self.assertEqual(upload.call_args.kwargs["resource_type"], "video")

    @patch("apps.posts.storage.uploader.upload")
    def test_post_media_storage_rewinds_screen_recording_before_video_upload(self, upload):
        storage = PostMedia._meta.get_field("file").storage
        video = SimpleUploadedFile(
            "Screen Recording 2026-06-11 192126.mp4",
            b"video-bytes",
            content_type="video/mp4",
        )
        video.read()
        offsets = []

        def record_upload(content, **options):
            offsets.append(content.tell())
            self.assertEqual(options["resource_type"], "video")
            return {"public_id": "posts/2026/screen-recording"}

        upload.side_effect = record_upload

        saved_name = storage._save(
            "posts/2026/Screen Recording 2026-06-11 192126.mp4",
            video,
        )

        self.assertEqual(saved_name, "__video__/posts/2026/screen-recording")
        self.assertEqual(offsets, [0])

    @patch("apps.posts.storage.uploader.upload")
    def test_post_media_storage_uses_video_type_from_uploaded_content_type(self, upload):
        storage = PostMedia._meta.get_field("file").storage
        upload.return_value = {"public_id": "posts/2026/downloaded-video"}
        video = SimpleUploadedFile(
            "upload",
            b"video-bytes",
            content_type="video/mp4",
        )

        saved_name = storage._save("posts/2026/upload", video)

        self.assertEqual(saved_name, "__video__/posts/2026/downloaded-video")
        self.assertEqual(upload.call_args.kwargs["resource_type"], "video")

    def test_instagram_image_url_includes_cloudinary_image_format(self):
        media = SimpleNamespace(
            media_type="IMAGE",
            mime_type="image/jpeg",
            file=SimpleNamespace(
                url=(
                    "https://res.cloudinary.com/example/image/upload/"
                    "posts/2026/photo"
                )
            ),
        )

        self.assertEqual(
            MetaPublisher._instagram_media_url(media),
            (
                "https://res.cloudinary.com/example/image/upload/"
                "posts/2026/photo.jpg"
            ),
        )

    @patch("apps.posts.publishing.meta.InstagramAPIClient")
    @patch("apps.posts.publishing.meta.decrypt_instagram_token")
    @patch("apps.posts.publishing.meta.get_active_instagram_credential")
    def test_instagram_image_story_uses_canonical_image_url(
        self,
        get_credential,
        decrypt_token,
        client_class,
    ):
        account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="instagram-user-story",
            account_name="Instagram",
        )
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            publish_type=PostPublishType.NOW,
            status=PostStatus.PUBLISHING,
        )
        target = PostPlatform.objects.create(
            post=post,
            platform=SocialPlatform.INSTAGRAM,
            social_account=account,
            content_type="STORY",
        )
        get_credential.return_value = SimpleNamespace(
            encrypted_access_token="encrypted-token",
        )
        decrypt_token.return_value = "access-token"
        client_class.return_value.graph_post.return_value = {"id": "story-container"}

        with patch.object(
            MetaPublisher,
            "_media",
            return_value=[
                SimpleNamespace(
                    media_type="IMAGE",
                    mime_type="image/jpeg",
                    file=SimpleNamespace(
                        url="https://res.cloudinary.com/example/image/upload/posts/2026/story"
                    ),
                )
            ],
        ):
            with self.assertRaises(MediaProcessingPending):
                MetaPublisher().publish_instagram(post_platform=target)

        self.assertEqual(
            client_class.return_value.graph_post.call_args.kwargs["data"]["image_url"],
            "https://res.cloudinary.com/example/image/upload/posts/2026/story.jpg",
        )

    @patch("apps.posts.publishing.meta.InstagramAPIClient")
    @patch("apps.posts.publishing.meta.decrypt_instagram_token")
    @patch("apps.posts.publishing.meta.get_active_instagram_credential")
    def test_instagram_image_story_retries_transient_image_delivery_rejection(
        self,
        get_credential,
        decrypt_token,
        client_class,
    ):
        account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="instagram-story-retry",
            account_name="Instagram",
        )
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            publish_type=PostPublishType.NOW,
            status=PostStatus.PUBLISHING,
        )
        target = PostPlatform.objects.create(
            post=post,
            platform=SocialPlatform.INSTAGRAM,
            social_account=account,
            content_type="STORY",
        )
        get_credential.return_value = SimpleNamespace(
            encrypted_access_token="encrypted-token",
        )
        decrypt_token.return_value = "access-token"
        client_class.return_value.graph_post.side_effect = InstagramAPIError(
            "Instagram rejected the source image.",
            error_payload={"error": {"code": 9004}},
        )

        with patch.object(
            MetaPublisher,
            "_media",
            return_value=[
                SimpleNamespace(
                    media_type="IMAGE",
                    mime_type="image/jpeg",
                    file=SimpleNamespace(
                        url="https://res.cloudinary.com/example/image/upload/posts/2026/story"
                    ),
                )
            ],
        ):
            with self.assertRaises(MediaProcessingPending):
                MetaPublisher().publish_instagram(post_platform=target)

        self.assertEqual(
            client_class.return_value.graph_post.call_args.kwargs["data"]["image_url"],
            "https://res.cloudinary.com/example/image/upload/posts/2026/story.jpg",
        )

    @patch("apps.posts.publishing.meta.MetaCredentialService.get_access_token")
    @patch("apps.posts.publishing.meta.MetaAPIClient")
    def test_facebook_video_story_uses_video_stories_endpoint(
        self,
        client_class,
        get_token,
    ):
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            publish_type=PostPublishType.NOW,
            status=PostStatus.PUBLISHING,
        )
        target = PostPlatform.objects.create(
            post=post,
            platform=SocialPlatform.FACEBOOK,
            social_account=self.account,
            content_type="STORY",
        )
        get_token.return_value = "access-token"
        client_class.return_value.post.side_effect = [
            {
                "video_id": "story-video-1",
                "upload_url": "https://upload.example/story-video",
            },
            {"id": "story-1"},
        ]

        with patch.object(
            MetaPublisher,
            "_media",
            return_value=[
                SimpleNamespace(
                    media_type="VIDEO",
                    file=SimpleNamespace(
                        url="https://media.example/story.mp4",
                        size=100,
                        open=lambda mode: None,
                        close=lambda: None,
                    ),
                    file_size=100,
                )
            ],
        ):
            MetaPublisher().publish_facebook(post_platform=target)

        self.assertEqual(
            client_class.return_value.post.call_args_list[0].args[0],
            "/page-1/video_stories",
        )
        self.assertEqual(
            client_class.return_value.post.call_args_list[0].kwargs["data"],
            {"upload_phase": "START"},
        )
        upload_call = client_class.return_value.upload_reel_video.call_args
        self.assertEqual(upload_call.args[0], "https://upload.example/story-video")
        self.assertEqual(upload_call.kwargs["access_token"], "access-token")
        self.assertEqual(upload_call.kwargs["file_size"], 100)
        self.assertEqual(
            client_class.return_value.post.call_args_list[1].args[0],
            "/page-1/video_stories",
        )
        self.assertEqual(
            client_class.return_value.post.call_args_list[1].kwargs["data"],
            {
                "upload_phase": "FINISH",
                "video_id": "story-video-1",
                "video_state": "PUBLISHED",
            },
        )

    @patch("apps.posts.publishing.meta.MetaCredentialService.get_access_token")
    @patch("apps.posts.publishing.meta.MetaAPIClient")
    def test_facebook_video_story_requires_upload_session(
        self,
        client_class,
        get_token,
    ):
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            publish_type=PostPublishType.NOW,
            status=PostStatus.PUBLISHING,
        )
        target = PostPlatform.objects.create(
            post=post,
            platform=SocialPlatform.FACEBOOK,
            social_account=self.account,
            content_type="STORY",
        )
        get_token.return_value = "access-token"
        client_class.return_value.post.return_value = {"video_id": "story-video-1"}

        with patch.object(
            MetaPublisher,
            "_media",
            return_value=[
                SimpleNamespace(
                    media_type="VIDEO",
                    file=SimpleNamespace(
                        url="https://media.example/story.mp4",
                        size=100,
                    ),
                    file_size=100,
                )
            ],
        ):
            with self.assertRaises(ProviderPublishingError):
                MetaPublisher().publish_facebook(post_platform=target)

        client_class.return_value.upload_reel_video.assert_not_called()

    @patch("apps.posts.publishing.meta.MetaCredentialService.get_access_token")
    @patch("apps.posts.publishing.meta.MetaAPIClient")
    def test_facebook_image_story_uses_photo_stories_endpoint(
        self,
        client_class,
        get_token,
    ):
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            publish_type=PostPublishType.NOW,
            status=PostStatus.PUBLISHING,
        )
        target = PostPlatform.objects.create(
            post=post,
            platform=SocialPlatform.FACEBOOK,
            social_account=self.account,
            content_type="STORY",
        )
        get_token.return_value = "access-token"
        client_class.return_value.post.side_effect = [
            {"id": "story-photo-1"},
            {"id": "story-1"},
        ]

        with patch.object(
            MetaPublisher,
            "_media",
            return_value=[
                SimpleNamespace(
                    media_type="IMAGE",
                    file=SimpleNamespace(url="https://media.example/story.jpg"),
                )
            ],
        ):
            MetaPublisher().publish_facebook(post_platform=target)

        self.assertEqual(
            client_class.return_value.post.call_args_list[1].args[0],
            "/page-1/photo_stories",
        )

    @patch("apps.posts.tasks.cache")
    @patch("apps.posts.tasks.get_publisher")
    def test_failed_target_marks_post_failed(self, get_publisher, task_cache):
        account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="instagram-user-2",
            account_name="Instagram",
        )
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            caption="Will fail",
            publish_type=PostPublishType.NOW,
            status=PostStatus.PUBLISHING,
        )
        target = PostPlatform.objects.create(
            post=post,
            platform=SocialPlatform.INSTAGRAM,
            social_account=account,
            content_type="POST",
        )
        get_publisher.return_value.publish.side_effect = PublishingValidationError(
            "Instagram rejected the image.",
        )
        task_cache.add.return_value = True

        publish_post_task.run(str(post.id))

        target.refresh_from_db()
        post.refresh_from_db()
        self.assertEqual(target.status, PostStatus.FAILED)
        self.assertEqual(target.error_message, "Instagram rejected the image.")
        self.assertEqual(post.status, PostStatus.FAILED)
        self.assertEqual(post.error_message, "Instagram rejected the image.")
