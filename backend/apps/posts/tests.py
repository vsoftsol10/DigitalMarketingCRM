from datetime import timedelta
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from celery.exceptions import Retry
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import TestCase
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.activities.models import ActivityEventType, ActivityLog, ActivitySource
from apps.integrations.instagram.exceptions import InstagramAPIError
from apps.organizations.models import Organization
from apps.social_accounts.models import SocialAccount, SocialAccountStatus, SocialPlatform

from .models import Post, PostMedia, PostPlatform, PostPublishType, PostStatus
from .publishing.exceptions import (
    MediaProcessingPending,
    ProviderPublishingError,
    PublishingValidationError,
)
from .publishing.meta import MetaPublisher
from .serializers import PostCreateSerializer
from .services import (
    create_post,
    delete_post,
    delete_post_target,
    publish_post_now,
    publish_post_target_now,
    retry_post_target,
    schedule_post,
    schedule_post_target,
    validate_target_accounts,
)
from .tasks import (
    _pending_retry_countdown,
    dispatch_due_posts_task,
    publish_post_task,
    reconcile_ambiguous_instagram_publishes_task,
)


def image_file():
    buffer = BytesIO()
    Image.new("RGB", (20, 20)).save(buffer, format="JPEG")
    return SimpleUploadedFile("post.jpg", buffer.getvalue(), content_type="image/jpeg")


class CalendarPostActionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="calendar-owner@example.com", first_name="Owner", password="password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-CALENDAR-ACTIONS", name="Calendar Actions",
            slug="calendar-actions", industry="Retail", created_by=self.user,
        )
        self.account = SocialAccount.objects.create(
            organization=self.organization, platform=SocialPlatform.FACEBOOK,
            platform_account_id="calendar-page", account_name="Calendar Page",
        )

    def create_post(self, status=PostStatus.DRAFT):
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            publish_type=PostPublishType.DRAFT,
            status=status,
        )
        target = PostPlatform.objects.create(
            post=post,
            social_account=self.account,
            platform=SocialPlatform.FACEBOOK,
            content_type="POST",
            status=PostStatus.DRAFT,
        )
        return post, target

    @patch("apps.posts.services.validate_target_accounts")
    def test_draft_can_be_scheduled_only_for_a_future_time(self, validate_targets):
        post, target = self.create_post()
        future = timezone.localtime(timezone.now() + timedelta(hours=1))
        scheduled = schedule_post(
            post_id=post.id,
            organization_id=self.organization.id,
            publish_date=future.date(),
            publish_time=future.time(),
            timezone_name="Asia/Kolkata",
        )
        self.assertEqual(scheduled.status, PostStatus.SCHEDULED)
        self.assertEqual(scheduled.publish_type, PostPublishType.SCHEDULE)
        target.refresh_from_db()
        self.assertEqual(target.status, PostStatus.SCHEDULED)
        self.assertEqual(target.scheduled_at, scheduled.scheduled_at)
        self.assertEqual(target.scheduled_timezone, "Asia/Kolkata")
        validate_targets.assert_called_once()

        past_post, _past_target = self.create_post()
        with self.assertRaisesMessage(ValueError, "future"):
            schedule_post(
                post_id=past_post.id,
                organization_id=self.organization.id,
                publish_date=timezone.localdate(),
                publish_time=(timezone.localtime(timezone.now()) - timedelta(minutes=1)).time(),
                timezone_name="Asia/Kolkata",
            )

    def test_schedule_rejects_non_draft_post(self):
        post, _target = self.create_post(status=PostStatus.FAILED)
        future = timezone.localtime(timezone.now() + timedelta(hours=1))
        with self.assertRaisesMessage(ValueError, "draft"):
            schedule_post(
                post_id=post.id,
                organization_id=self.organization.id,
                publish_date=future.date(), publish_time=future.time(), timezone_name="Asia/Kolkata",
            )

    @patch("apps.posts.services.validate_target_accounts")
    def test_scheduled_post_can_be_rescheduled(self, validate_targets):
        post, _target = self.create_post(status=PostStatus.SCHEDULED)
        post.publish_type = PostPublishType.SCHEDULE
        post.scheduled_at = timezone.now() + timedelta(hours=1)
        post.save()
        future = timezone.localtime(timezone.now() + timedelta(hours=2))

        schedule_post(
            post_id=post.id,
            organization_id=self.organization.id,
            publish_date=future.date(),
            publish_time=future.time(),
            timezone_name="Asia/Kolkata",
            reschedule=True,
        )

        post.refresh_from_db()
        self.assertEqual(post.status, PostStatus.SCHEDULED)
        self.assertEqual(post.timezone, "Asia/Kolkata")
        validate_targets.assert_called_once()

    @patch("apps.posts.services.validate_target_accounts")
    def test_calendar_target_schedule_does_not_change_sibling_target(self, validate_targets):
        post, instagram_target, facebook_target = self.create_two_target_post()
        future = timezone.localtime(timezone.now() + timedelta(hours=2))

        schedule_post_target(
            post_id=post.id,
            organization_id=self.organization.id,
            target_id=instagram_target.id,
            publish_date=future.date(),
            publish_time=future.time(),
            timezone_name="Asia/Kolkata",
        )

        post.refresh_from_db()
        instagram_target.refresh_from_db()
        facebook_target.refresh_from_db()
        self.assertEqual(instagram_target.status, PostStatus.SCHEDULED)
        self.assertIsNotNone(instagram_target.scheduled_at)
        self.assertEqual(facebook_target.status, PostStatus.DRAFT)
        self.assertIsNone(facebook_target.scheduled_at)
        self.assertEqual(post.status, PostStatus.DRAFT)
        validate_targets.assert_called_once()

    @patch("apps.posts.services.validate_target_accounts")
    def test_calendar_target_reschedule_does_not_change_sibling_target(self, validate_targets):
        post, instagram_target, facebook_target = self.create_two_target_post()
        instagram_target.status = PostStatus.SCHEDULED
        instagram_target.scheduled_at = timezone.now() + timedelta(hours=1)
        instagram_target.scheduled_timezone = "Asia/Kolkata"
        instagram_target.save()
        future = timezone.localtime(timezone.now() + timedelta(hours=3))

        schedule_post_target(
            post_id=post.id,
            organization_id=self.organization.id,
            target_id=instagram_target.id,
            publish_date=future.date(),
            publish_time=future.time(),
            timezone_name="Asia/Kolkata",
        )

        instagram_target.refresh_from_db()
        facebook_target.refresh_from_db()
        self.assertEqual(instagram_target.status, PostStatus.SCHEDULED)
        self.assertEqual(facebook_target.status, PostStatus.DRAFT)
        self.assertIsNone(facebook_target.scheduled_at)
        validate_targets.assert_called_once()

    def test_calendar_target_schedule_rejects_past_datetime(self):
        post, instagram_target, _facebook_target = self.create_two_target_post()
        past = timezone.localtime(timezone.now() - timedelta(minutes=1))

        with self.assertRaisesMessage(ValueError, "future"):
            schedule_post_target(
                post_id=post.id,
                organization_id=self.organization.id,
                target_id=instagram_target.id,
                publish_date=past.date(),
                publish_time=past.time(),
                timezone_name="Asia/Kolkata",
            )

    @patch("apps.posts.services.validate_target_accounts")
    @patch("apps.posts.services.enqueue_post_publication")
    def test_draft_publish_now_transitions_and_enqueues_after_commit(self, enqueue, _validate_targets):
        post, _target = self.create_post()

        with self.captureOnCommitCallbacks(execute=True):
            publish_post_now(post_id=post.id, organization_id=self.organization.id)

        post.refresh_from_db()
        self.assertEqual(post.status, PostStatus.PUBLISHING)
        self.assertEqual(post.publish_type, PostPublishType.NOW)
        self.assertIsNone(post.scheduled_at)
        enqueue.assert_called_once_with(post.id)

    @patch("apps.posts.services.validate_target_accounts")
    @patch("apps.posts.services.enqueue_post_publication")
    def test_draft_publish_now_does_not_enqueue_when_transaction_rolls_back(self, enqueue, _validate_targets):
        post, _target = self.create_post()

        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                publish_post_now(post_id=post.id, organization_id=self.organization.id)
                raise RuntimeError("roll back action")

        post.refresh_from_db()
        self.assertEqual(post.status, PostStatus.DRAFT)
        enqueue.assert_not_called()

    @patch("apps.posts.services.validate_target_accounts")
    @patch("apps.posts.services.enqueue_post_publication")
    def test_concurrent_publish_now_guard_does_not_enqueue_duplicate_publication(self, enqueue, _validate_targets):
        post, _target = self.create_post()

        with self.captureOnCommitCallbacks(execute=True):
            publish_post_now(post_id=post.id, organization_id=self.organization.id)

        with self.assertRaisesMessage(ValueError, "draft or scheduled"):
            publish_post_now(post_id=post.id, organization_id=self.organization.id)

        enqueue.assert_called_once_with(post.id)

    def test_published_post_cannot_be_published_now_again(self):
        post, _target = self.create_post(status=PostStatus.PUBLISHED)
        with self.assertRaisesMessage(ValueError, "draft or scheduled"):
            publish_post_now(post_id=post.id, organization_id=self.organization.id)

    def create_two_target_post(self):
        instagram_account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="calendar-instagram",
            account_name="Calendar Instagram",
        )
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            publish_type=PostPublishType.DRAFT,
            status=PostStatus.DRAFT,
        )
        instagram_target = PostPlatform.objects.create(
            post=post,
            social_account=instagram_account,
            platform=SocialPlatform.INSTAGRAM,
            content_type="POST",
            status=PostStatus.DRAFT,
        )
        facebook_target = PostPlatform.objects.create(
            post=post,
            social_account=self.account,
            platform=SocialPlatform.FACEBOOK,
            content_type="POST",
            status=PostStatus.DRAFT,
        )
        return post, instagram_target, facebook_target

    @patch("apps.posts.services.validate_target_accounts")
    @patch("apps.posts.services.enqueue_post_target_publication")
    def test_instagram_target_publish_now_does_not_enqueue_facebook(self, enqueue, _validate):
        post, instagram_target, facebook_target = self.create_two_target_post()

        with self.captureOnCommitCallbacks(execute=True):
            publish_post_target_now(
                post_id=post.id,
                organization_id=self.organization.id,
                target_id=instagram_target.id,
            )

        facebook_target.refresh_from_db()
        self.assertEqual(facebook_target.status, PostStatus.DRAFT)
        enqueue.assert_called_once_with(post.id, instagram_target.id)

    @patch("apps.posts.services.validate_target_accounts")
    @patch("apps.posts.services.enqueue_post_target_publication")
    def test_facebook_target_publish_now_does_not_enqueue_instagram(self, enqueue, _validate):
        post, instagram_target, facebook_target = self.create_two_target_post()

        with self.captureOnCommitCallbacks(execute=True):
            publish_post_target_now(
                post_id=post.id,
                organization_id=self.organization.id,
                target_id=facebook_target.id,
            )

        instagram_target.refresh_from_db()
        self.assertEqual(instagram_target.status, PostStatus.DRAFT)
        enqueue.assert_called_once_with(post.id, facebook_target.id)

    @patch("apps.posts.services.validate_target_accounts")
    @patch("apps.posts.services.enqueue_post_target_publication")
    def test_target_publish_now_roll_back_does_not_enqueue(self, enqueue, _validate):
        post, instagram_target, _facebook_target = self.create_two_target_post()

        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                publish_post_target_now(
                    post_id=post.id,
                    organization_id=self.organization.id,
                    target_id=instagram_target.id,
                )
                raise RuntimeError("roll back action")

        post.refresh_from_db()
        self.assertEqual(post.status, PostStatus.DRAFT)
        enqueue.assert_not_called()

    def test_deleting_instagram_target_preserves_facebook_target_and_shared_media(self):
        post, instagram_target, facebook_target = self.create_two_target_post()
        media = PostMedia.objects.create(
            post=post,
            media_type="IMAGE",
            file="posts/shared-image.jpg",
        )

        delete_post_target(
            post_id=post.id,
            organization_id=self.organization.id,
            target_id=instagram_target.id,
        )

        instagram_target.refresh_from_db()
        facebook_target.refresh_from_db()
        media.refresh_from_db()
        self.assertTrue(instagram_target.is_deleted)
        self.assertFalse(facebook_target.is_deleted)
        self.assertFalse(media.is_deleted)

    def test_deleting_facebook_target_preserves_instagram_target(self):
        post, instagram_target, facebook_target = self.create_two_target_post()

        delete_post_target(
            post_id=post.id,
            organization_id=self.organization.id,
            target_id=facebook_target.id,
        )

        instagram_target.refresh_from_db()
        facebook_target.refresh_from_db()
        self.assertFalse(instagram_target.is_deleted)
        self.assertTrue(facebook_target.is_deleted)

    @patch("apps.posts.services.enqueue_post_target_publication")
    def test_failed_target_retry_clears_schedule_and_queues_only_target(self, enqueue):
        post, failed_target, other_target = self.create_two_target_post()
        post.status = PostStatus.FAILED
        post.scheduled_at = timezone.now() + timedelta(days=1)
        post.save()
        failed_target.status = PostStatus.FAILED
        failed_target.provider_container_id = "resume-container"
        failed_target.provider_state = {"session": "resume"}
        failed_target.save()

        with self.captureOnCommitCallbacks(execute=True):
            retry_post_target(
                post_id=post.id,
                organization_id=self.organization.id,
                target_id=failed_target.id,
            )

        post.refresh_from_db()
        failed_target.refresh_from_db()
        other_target.refresh_from_db()
        self.assertIsNone(post.scheduled_at)
        self.assertEqual(failed_target.provider_container_id, "resume-container")
        self.assertEqual(failed_target.provider_state, {"session": "resume"})
        self.assertEqual(other_target.status, PostStatus.DRAFT)
        enqueue.assert_called_once_with(post.id, failed_target.id)

    def test_published_target_cannot_be_published_retried_or_deleted(self):
        post, target = self.create_post(status=PostStatus.PUBLISHED)
        target.status = PostStatus.PUBLISHED
        target.save()

        with self.assertRaises(ValueError):
            publish_post_target_now(
                post_id=post.id,
                organization_id=self.organization.id,
                target_id=target.id,
            )
        with self.assertRaises(ValueError):
            retry_post_target(
                post_id=post.id,
                organization_id=self.organization.id,
                target_id=target.id,
            )
        with self.assertRaises(ValueError):
            delete_post_target(
                post_id=post.id,
                organization_id=self.organization.id,
                target_id=target.id,
            )

    def test_calendar_api_uses_target_status_not_aggregate_post_status(self):
        post, instagram_target, facebook_target = self.create_two_target_post()
        post.status = PostStatus.FAILED
        post.save()
        instagram_target.status = PostStatus.PUBLISHING
        instagram_target.save()

        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get("/api/posts/calendar/events/")

        self.assertEqual(response.status_code, 200)
        statuses = {
            event["id"]: event["status"]
            for event in response.json()["data"]
        }
        self.assertEqual(statuses[str(instagram_target.id)], PostStatus.PUBLISHING)
        self.assertEqual(statuses[str(facebook_target.id)], PostStatus.DRAFT)

    def test_calendar_api_includes_unresolved_target_status(self):
        post, instagram_target, _facebook_target = self.create_two_target_post()
        post.status = PostStatus.PUBLISHING
        post.save()
        instagram_target.status = PostStatus.UNRESOLVED
        instagram_target.save()

        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get("/api/posts/calendar/events/")

        self.assertEqual(response.status_code, 200)
        statuses = {
            event["id"]: event["status"]
            for event in response.json()["data"]
        }
        self.assertEqual(statuses[str(instagram_target.id)], PostStatus.UNRESOLVED)

    @patch("apps.posts.tasks.get_publisher")
    def test_target_publish_task_success_transitions_to_published(self, get_publisher):
        post, instagram_target, facebook_target = self.create_two_target_post()
        post.status = PostStatus.PUBLISHING
        post.save()
        instagram_target.status = PostStatus.PUBLISHING
        instagram_target.save()
        facebook_target.status = PostStatus.SCHEDULED
        facebook_target.scheduled_at = timezone.now() + timedelta(hours=1)
        facebook_target.scheduled_timezone = "UTC"
        facebook_target.save()
        get_publisher.return_value.publish.return_value = {
            "external_post_id": "instagram-success",
        }

        publish_post_task.run(str(post.id), str(instagram_target.id))

        instagram_target.refresh_from_db()
        facebook_target.refresh_from_db()
        self.assertEqual(instagram_target.status, PostStatus.PUBLISHED)
        self.assertEqual(facebook_target.status, PostStatus.SCHEDULED)
        activities = ActivityLog.objects.filter(
            post_platform=instagram_target,
            event_type=ActivityEventType.POST_PUBLISHED,
        )
        self.assertEqual(activities.count(), 1)
        self.assertEqual(activities.get().source, ActivitySource.SYSTEM)

        publish_post_task.run(str(post.id), str(instagram_target.id))
        self.assertEqual(activities.count(), 1)

    @patch("apps.posts.tasks.get_publisher")
    def test_target_task_runs_when_parent_is_partially_published(self, get_publisher):
        post, instagram_target, facebook_target = self.create_two_target_post()
        post.status = PostStatus.PARTIALLY_PUBLISHED
        post.save()
        instagram_target.status = PostStatus.PUBLISHED
        instagram_target.save()
        facebook_target.status = PostStatus.PUBLISHING
        facebook_target.save()
        get_publisher.return_value.publish.return_value = {
            "external_post_id": "facebook-success",
        }

        publish_post_task.run(str(post.id), str(facebook_target.id))

        facebook_target.refresh_from_db()
        self.assertEqual(facebook_target.status, PostStatus.PUBLISHED)
        get_publisher.return_value.publish.assert_called_once()

    @patch("apps.posts.tasks.publish_post_task.delay")
    def test_due_target_dispatch_ignores_parent_partial_status_without_duplicate_queue(self, delay):
        post, instagram_target, facebook_target = self.create_two_target_post()
        post.status = PostStatus.PARTIALLY_PUBLISHED
        post.save()
        instagram_target.status = PostStatus.PUBLISHED
        instagram_target.save()
        facebook_target.status = PostStatus.SCHEDULED
        facebook_target.scheduled_at = timezone.now() - timedelta(minutes=1)
        facebook_target.scheduled_timezone = "UTC"
        facebook_target.save()

        dispatch_due_posts_task.run()

        facebook_target.refresh_from_db()
        self.assertEqual(facebook_target.status, PostStatus.PUBLISHING)
        delay.assert_called_once_with(str(post.id), str(facebook_target.id))

    @patch("apps.posts.tasks.get_publisher")
    def test_target_publish_task_failure_transitions_only_target_to_failed(self, get_publisher):
        post, instagram_target, facebook_target = self.create_two_target_post()
        post.status = PostStatus.PUBLISHING
        post.save()
        instagram_target.status = PostStatus.PUBLISHING
        instagram_target.save()
        get_publisher.return_value.publish.side_effect = RuntimeError("Provider failed")

        publish_post_task.run(str(post.id), str(instagram_target.id))

        instagram_target.refresh_from_db()
        facebook_target.refresh_from_db()
        self.assertEqual(instagram_target.status, PostStatus.FAILED)
        self.assertEqual(facebook_target.status, PostStatus.DRAFT)
        activities = ActivityLog.objects.filter(
            post_platform=instagram_target,
            event_type=ActivityEventType.POST_FAILED,
        )
        self.assertEqual(activities.count(), 1)
        self.assertEqual(activities.get().source, ActivitySource.SYSTEM)

    @patch("apps.posts.tasks._pending_retry_limit_reached", return_value=True)
    @patch("apps.posts.tasks.get_publisher")
    def test_exhausted_media_processing_marks_target_failed_and_preserves_resume_state(
        self,
        get_publisher,
        _limit_reached,
    ):
        post, instagram_target, facebook_target = self.create_two_target_post()
        post.status = PostStatus.PUBLISHING
        post.save()
        instagram_target.status = PostStatus.PUBLISHING
        instagram_target.provider_container_id = "instagram-container"
        instagram_target.provider_state = {"carousel_children": ["child-1"]}
        instagram_target.save()
        get_publisher.return_value.publish.side_effect = MediaProcessingPending(
            "Instagram media is still processing.",
        )

        publish_post_task.run(str(post.id), str(instagram_target.id))

        instagram_target.refresh_from_db()
        facebook_target.refresh_from_db()
        self.assertEqual(instagram_target.status, PostStatus.FAILED)
        self.assertIn("retry limit", instagram_target.error_message)
        self.assertEqual(instagram_target.provider_container_id, "instagram-container")
        self.assertEqual(
            instagram_target.provider_state,
            {"carousel_children": ["child-1"]},
        )
        self.assertEqual(facebook_target.status, PostStatus.DRAFT)
        get_publisher.return_value.publish.assert_called_once()
        self.assertTrue(
            ActivityLog.objects.filter(
                post_platform=instagram_target,
                event_type=ActivityEventType.POST_FAILED,
                source=ActivitySource.SYSTEM,
            ).exists()
        )

    @patch("apps.posts.tasks.cache")
    @patch("apps.posts.tasks.get_publisher")
    @patch("apps.posts.tasks.publish_post_task.retry", side_effect=Retry())
    def test_pre_container_instagram_pending_retries_then_publishes(
        self,
        retry,
        get_publisher,
        task_cache,
    ):
        post, instagram_target, facebook_target = self.create_two_target_post()
        post.status = PostStatus.PUBLISHING
        post.save()
        instagram_target.status = PostStatus.PUBLISHING
        instagram_target.save()
        task_cache.add.return_value = True
        publisher = get_publisher.return_value
        publisher.publish.side_effect = MediaProcessingPending(
            "Instagram image media is not available for processing yet.",
        )

        with self.assertRaises(Retry):
            publish_post_task.run(str(post.id), str(instagram_target.id))

        instagram_target.refresh_from_db()
        self.assertEqual(instagram_target.status, PostStatus.PUBLISHING)
        self.assertEqual(instagram_target.provider_container_id, "")
        self.assertEqual(instagram_target.provider_state, {})
        self.assertEqual(instagram_target.attempt_count, 1)
        retry.assert_called_once()

        publisher.publish.side_effect = None
        publisher.publish.return_value = {
            "external_post_id": "instagram-success",
            "provider_container_id": "container-1",
        }
        publish_post_task.run(str(post.id), str(instagram_target.id))

        instagram_target.refresh_from_db()
        facebook_target.refresh_from_db()
        self.assertEqual(instagram_target.status, PostStatus.PUBLISHED)
        self.assertEqual(instagram_target.external_post_id, "instagram-success")
        self.assertEqual(instagram_target.provider_container_id, "container-1")
        self.assertEqual(instagram_target.attempt_count, 2)
        self.assertEqual(facebook_target.status, PostStatus.DRAFT)
        self.assertEqual(publisher.publish.call_count, 2)

    @patch("apps.posts.tasks.cache")
    @patch("apps.posts.tasks._pending_retry_limit_reached", return_value=True)
    @patch("apps.posts.tasks.get_publisher")
    def test_pre_container_instagram_pending_exhaustion_marks_failed(
        self,
        get_publisher,
        _limit_reached,
        task_cache,
    ):
        post, instagram_target, facebook_target = self.create_two_target_post()
        post.status = PostStatus.PUBLISHING
        post.save()
        instagram_target.status = PostStatus.PUBLISHING
        instagram_target.publish_started_at = timezone.now()
        instagram_target.save()
        task_cache.add.return_value = True
        get_publisher.return_value.publish.side_effect = MediaProcessingPending(
            "Instagram image media is not available for processing yet.",
        )

        publish_post_task.run(str(post.id), str(instagram_target.id))

        instagram_target.refresh_from_db()
        facebook_target.refresh_from_db()
        self.assertEqual(instagram_target.status, PostStatus.FAILED)
        self.assertEqual(instagram_target.provider_container_id, "")
        self.assertEqual(instagram_target.provider_state, {})
        self.assertIn("retry limit", instagram_target.error_message)
        self.assertEqual(facebook_target.status, PostStatus.DRAFT)
        get_publisher.return_value.publish.assert_called_once()
        self.assertTrue(
            ActivityLog.objects.filter(
                post_platform=instagram_target,
                event_type=ActivityEventType.POST_FAILED,
                source=ActivitySource.SYSTEM,
            ).exists()
        )

    @patch("apps.posts.tasks.get_publisher")
    def test_ambiguous_instagram_publish_remains_unresolved_without_retrying(
        self,
        get_publisher,
    ):
        post, instagram_target, facebook_target = self.create_two_target_post()
        post.status = PostStatus.PUBLISHING
        post.save()
        instagram_target.status = PostStatus.PUBLISHING
        instagram_target.provider_container_id = "instagram-container"
        instagram_target.provider_state = {"resume": "safe"}
        instagram_target.save()
        outcome = ProviderPublishingError(
            "Instagram publish outcome could not be confirmed. The existing "
            "provider container was preserved; manual reconciliation may be "
            "required. provider_message=Application request limit reached "
            "provider_code=4 error_subcode=2207051 http_status=403 "
            "fbtrace_id=trace-2207051"
        )
        outcome.ambiguous_media_publish = True
        get_publisher.return_value.publish.side_effect = outcome

        publish_post_task.run(str(post.id), str(instagram_target.id))

        instagram_target.refresh_from_db()
        facebook_target.refresh_from_db()
        self.assertEqual(instagram_target.status, PostStatus.UNRESOLVED)
        self.assertIn("outcome could not be confirmed", instagram_target.error_message)
        self.assertIn("provider_code=4", instagram_target.error_message)
        self.assertIn("error_subcode=2207051", instagram_target.error_message)
        self.assertIn("http_status=403", instagram_target.error_message)
        self.assertIn("fbtrace_id=trace-2207051", instagram_target.error_message)
        self.assertEqual(instagram_target.provider_container_id, "instagram-container")
        self.assertEqual(instagram_target.provider_state, {"resume": "safe"})
        self.assertEqual(facebook_target.status, PostStatus.DRAFT)
        self.assertFalse(
            ActivityLog.objects.filter(
                post_platform=instagram_target,
                event_type=ActivityEventType.POST_FAILED,
            ).exists()
        )
        publish_post_task.run(str(post.id), str(instagram_target.id))
        get_publisher.return_value.publish.assert_called_once()

    @staticmethod
    def _mark_ambiguous_instagram_target(target):
        target.status = PostStatus.UNRESOLVED
        target.provider_container_id = "instagram-container"
        target.provider_state = {"resume": "safe"}
        target.error_message = (
            "Instagram publish outcome could not be confirmed. The existing "
            "provider container was preserved; manual reconciliation may be required."
        )
        target.save()

    @patch("apps.posts.tasks.InstagramAPIClient")
    @patch("apps.posts.tasks.decrypt_instagram_token", return_value="access-token")
    @patch("apps.posts.tasks.get_active_instagram_credential")
    def test_ambiguous_instagram_reconciliation_published_marks_target_published(
        self,
        get_credential,
        _decrypt_token,
        client_class,
    ):
        post, instagram_target, facebook_target = self.create_two_target_post()
        post.status = PostStatus.PUBLISHING
        post.save()
        self._mark_ambiguous_instagram_target(instagram_target)
        get_credential.return_value = SimpleNamespace(encrypted_access_token="encrypted")
        client_class.return_value.graph_get.return_value = {"status_code": "PUBLISHED"}
        client_class.return_value.last_response_status_code = 200

        reconcile_ambiguous_instagram_publishes_task.run()

        instagram_target.refresh_from_db()
        facebook_target.refresh_from_db()
        self.assertEqual(instagram_target.status, PostStatus.PUBLISHED)
        self.assertEqual(instagram_target.external_post_id, "")
        self.assertEqual(instagram_target.provider_container_id, "instagram-container")
        self.assertEqual(instagram_target.provider_state, {"resume": "safe"})
        self.assertEqual(instagram_target.error_message, "")
        self.assertEqual(facebook_target.status, PostStatus.DRAFT)
        client_class.return_value.graph_post.assert_not_called()
        activities = ActivityLog.objects.filter(
            post_platform=instagram_target,
            event_type=ActivityEventType.POST_PUBLISHED,
        )
        self.assertEqual(activities.count(), 1)

        reconcile_ambiguous_instagram_publishes_task.run()
        self.assertEqual(activities.count(), 1)

    @patch("apps.posts.tasks.InstagramAPIClient")
    @patch("apps.posts.tasks.decrypt_instagram_token", return_value="access-token")
    @patch("apps.posts.tasks.get_active_instagram_credential")
    def test_ambiguous_instagram_reconciliation_error_and_expired_remain_unresolved(
        self,
        get_credential,
        _decrypt_token,
        client_class,
    ):
        get_credential.return_value = SimpleNamespace(encrypted_access_token="encrypted")
        client_class.return_value.last_response_status_code = 200

        for status_code in ("ERROR", "EXPIRED"):
            with self.subTest(status_code=status_code):
                post, instagram_target, _facebook_target = self.create_two_target_post()
                post.status = PostStatus.PUBLISHING
                post.save()
                self._mark_ambiguous_instagram_target(instagram_target)
                client_class.return_value.graph_get.return_value = {
                    "status_code": status_code,
                }

                reconcile_ambiguous_instagram_publishes_task.run()

                instagram_target.refresh_from_db()
                self.assertEqual(instagram_target.status, PostStatus.UNRESOLVED)
                self.assertIn("outcome could not be confirmed", instagram_target.error_message)
                self.assertEqual(instagram_target.provider_container_id, "instagram-container")
                self.assertEqual(instagram_target.provider_state, {"resume": "safe"})

        client_class.return_value.graph_post.assert_not_called()

    @patch("apps.posts.tasks.InstagramAPIClient")
    @patch("apps.posts.tasks.decrypt_instagram_token", return_value="access-token")
    @patch("apps.posts.tasks.get_active_instagram_credential")
    def test_ambiguous_instagram_reconciliation_processing_states_remain_unresolved(
        self,
        get_credential,
        _decrypt_token,
        client_class,
    ):
        get_credential.return_value = SimpleNamespace(encrypted_access_token="encrypted")
        client_class.return_value.last_response_status_code = 200

        for status_code in ("IN_PROGRESS", "FINISHED", None):
            with self.subTest(status_code=status_code):
                post, instagram_target, _facebook_target = self.create_two_target_post()
                post.status = PostStatus.PUBLISHING
                post.save()
                self._mark_ambiguous_instagram_target(instagram_target)
                client_class.return_value.graph_get.return_value = {
                    "status_code": status_code,
                }

                reconcile_ambiguous_instagram_publishes_task.run()

                instagram_target.refresh_from_db()
                self.assertEqual(instagram_target.status, PostStatus.UNRESOLVED)
                self.assertTrue(instagram_target.error_message.startswith(
                    "Instagram publish outcome could not be confirmed."
                ))
                self.assertEqual(instagram_target.provider_container_id, "instagram-container")
                self.assertEqual(instagram_target.provider_state, {"resume": "safe"})

        client_class.return_value.graph_post.assert_not_called()

    @patch("apps.posts.tasks.InstagramAPIClient")
    def test_ambiguous_instagram_reconciliation_skips_terminal_targets(self, client_class):
        for status in (PostStatus.PUBLISHED, PostStatus.FAILED):
            with self.subTest(status=status):
                _post, instagram_target, _facebook_target = self.create_two_target_post()
                self._mark_ambiguous_instagram_target(instagram_target)
                instagram_target.status = status
                instagram_target.save()

                reconcile_ambiguous_instagram_publishes_task.run()

        client_class.return_value.graph_get.assert_not_called()

    @patch("apps.posts.services.validate_target_accounts")
    @patch("apps.posts.services.enqueue_post_publication")
    def test_publish_now_enqueues_after_commit(self, enqueue, _validate_targets):
        post, _target = self.create_post(status=PostStatus.SCHEDULED)
        post.publish_type = PostPublishType.SCHEDULE
        post.scheduled_at = timezone.now() + timedelta(hours=1)
        post.save()

        with self.captureOnCommitCallbacks(execute=True):
            publish_post_now(post_id=post.id, organization_id=self.organization.id)

        post.refresh_from_db()
        self.assertEqual(post.status, PostStatus.PUBLISHING)
        self.assertIsNone(post.scheduled_at)
        enqueue.assert_called_once_with(post.id)

    @patch("apps.posts.services.enqueue_post_target_publication")
    def test_retry_is_target_specific_and_preserves_provider_resume_state(self, enqueue):
        post, failed_target = self.create_post(status=PostStatus.FAILED)
        failed_target.status = PostStatus.FAILED
        failed_target.provider_container_id = "container-1"
        failed_target.provider_state = {"upload_session": "resume-1"}
        failed_target.error_message = "Temporary provider error"
        failed_target.save()
        published_target = PostPlatform.objects.create(
            post=post, social_account=None, platform=SocialPlatform.INSTAGRAM,
            content_type="POST", status=PostStatus.PUBLISHED, external_post_id="published-1",
        )

        with self.captureOnCommitCallbacks(execute=True):
            retry_post_target(
                post_id=post.id, organization_id=self.organization.id, target_id=failed_target.id,
            )

        failed_target.refresh_from_db()
        published_target.refresh_from_db()
        post.refresh_from_db()
        self.assertEqual(failed_target.status, PostStatus.DRAFT)
        self.assertEqual(failed_target.provider_container_id, "container-1")
        self.assertEqual(failed_target.provider_state, {"upload_session": "resume-1"})
        self.assertEqual(published_target.status, PostStatus.PUBLISHED)
        self.assertEqual(post.status, PostStatus.PUBLISHING)
        enqueue.assert_called_once_with(post.id, failed_target.id)

    @patch("apps.posts.tasks.get_publisher")
    def test_targeted_retry_task_never_republishes_a_published_target(self, get_publisher):
        post, retry_target = self.create_post(status=PostStatus.PUBLISHING)
        retry_target.status = PostStatus.DRAFT
        retry_target.save()
        published_target = PostPlatform.objects.create(
            post=post, social_account=None, platform=SocialPlatform.INSTAGRAM,
            content_type="POST", status=PostStatus.PUBLISHED, external_post_id="published-1",
        )
        publisher = get_publisher.return_value
        publisher.publish.return_value = {"external_post_id": "retry-result"}

        publish_post_task.run(str(post.id), str(retry_target.id))

        retry_target.refresh_from_db()
        published_target.refresh_from_db()
        self.assertEqual(retry_target.status, PostStatus.PUBLISHED)
        self.assertEqual(published_target.status, PostStatus.PUBLISHED)
        publisher.publish.assert_called_once()

    def test_retry_rejects_a_published_target(self):
        post, target = self.create_post(status=PostStatus.PUBLISHED)
        target.status = PostStatus.PUBLISHED
        target.save()
        with self.assertRaisesMessage(ValueError, "failed"):
            retry_post_target(post_id=post.id, organization_id=self.organization.id, target_id=target.id)

    def test_delete_rejects_a_post_claimed_for_publishing(self):
        post, target = self.create_post(status=PostStatus.PUBLISHING)
        target.status = PostStatus.PUBLISHING
        target.save()
        with self.assertRaisesMessage(ValueError, "currently publishing"):
            delete_post(post=post)
        post.refresh_from_db()
        self.assertFalse(post.is_deleted)

    def test_delete_rejects_a_published_post(self):
        post, _target = self.create_post(status=PostStatus.PUBLISHED)
        with self.assertRaisesMessage(ValueError, "Published"):
            delete_post(post=post)

    def test_action_endpoint_enforces_organization_ownership(self):
        post, _target = self.create_post()
        other_user = User.objects.create_user(
            email="calendar-other@example.com", first_name="Other", password="password",
        )
        client = APIClient()
        client.force_authenticate(user=other_user)
        response = client.post(
            f"/api/posts/organizations/{self.organization.organization_id}/{post.id}/publish-now/",
        )
        self.assertEqual(response.status_code, 403)


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
        self.api_client = APIClient()
        self.api_client.force_authenticate(user=self.user)

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

    @patch("apps.posts.services.validate_target_accounts")
    def test_create_schedule_sets_every_selected_target_scheduled(self, _validate_targets):
        instagram_account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="scheduled-instagram",
            account_name="Scheduled Instagram",
        )
        future = timezone.localtime(timezone.now() + timedelta(hours=1))

        post = create_post(
            organization=self.organization,
            created_by=self.user,
            validated_data={
                "targets": [
                    {"social_account": self.account.id, "content_type": "POST"},
                    {"social_account": instagram_account.id, "content_type": "POST"},
                ],
                "media": [],
                "caption": "Scheduled targets",
                "publish_type": PostPublishType.SCHEDULE,
                "publish_date": future.date(),
                "publish_time": future.time(),
                "timezone": "Asia/Kolkata",
            },
        )

        targets = list(post.platforms.order_by("social_account_id"))
        self.assertTrue(all(target.status == PostStatus.SCHEDULED for target in targets))
        self.assertTrue(all(target.scheduled_at == post.scheduled_at for target in targets))
        self.assertTrue(all(target.scheduled_timezone == "Asia/Kolkata" for target in targets))

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

    def test_instagram_container_in_progress_retries_without_publishing(self):
        api = SimpleNamespace(
            graph_get=MagicMock(return_value={"status_code": "IN_PROGRESS"}),
            graph_post=MagicMock(),
        )
        target = SimpleNamespace(provider_container_id="container-1")

        with self.assertRaises(MediaProcessingPending):
            MetaPublisher._publish_instagram_container(
                api=api,
                token="token",
                account_id="account-1",
                post_platform=target,
            )

        api.graph_post.assert_not_called()
        self.assertEqual(
            api.graph_get.call_args.kwargs["params"],
            {"fields": "status_code,status"},
        )

    def test_instagram_finished_container_calls_media_publish_once(self):
        api = SimpleNamespace(
            graph_get=MagicMock(return_value={"status_code": "FINISHED"}),
            graph_post=MagicMock(return_value={"id": "post-finished"}),
        )
        target = SimpleNamespace(provider_container_id="container-1")

        result = MetaPublisher._publish_instagram_container(
            api=api,
            token="token",
            account_id="account-1",
            post_platform=target,
        )

        self.assertEqual(result["external_post_id"], "post-finished")
        api.graph_post.assert_called_once_with(
            "account-1/media_publish",
            access_token="token",
            data={"creation_id": "container-1"},
        )

    def test_instagram_published_container_never_replays_media_publish(self):
        api = SimpleNamespace(
            graph_get=MagicMock(return_value={"status_code": "PUBLISHED"}),
            graph_post=MagicMock(),
        )
        target = SimpleNamespace(provider_container_id="container-1")

        result = MetaPublisher._publish_instagram_container(
            api=api,
            token="token",
            account_id="account-1",
            post_platform=target,
        )

        self.assertEqual(result["external_post_id"], "")
        self.assertEqual(result["provider_container_id"], "container-1")
        api.graph_post.assert_not_called()

    def test_instagram_media_publish_app_restriction_is_unresolved_without_retry(self):
        api = SimpleNamespace(
            graph_get=MagicMock(return_value={"status_code": "FINISHED"}),
            graph_post=MagicMock(side_effect=InstagramAPIError(
                "Application request limit reached.",
                status_code=403,
                error_payload={
                    "error": {
                        "code": 4,
                        "error_subcode": 2207051,
                        "message": "Application request limit reached",
                        "type": "OAuthException",
                        "fbtrace_id": "trace-2207051",
                        "access_token": "must-not-appear",
                        "client_secret": "must-not-appear",
                    }
                },
                usage_diagnostics={
                    "x-app-usage": {
                        "call_count": 81,
                        "total_cputime": 14,
                        "total_time": 7,
                    },
                },
            )),
        )
        target = SimpleNamespace(id="target-1", provider_container_id="container-1")

        with self.assertLogs("apps.posts.publishing.meta", level="WARNING") as logs:
            with self.assertRaises(ProviderPublishingError) as raised:
                MetaPublisher._publish_instagram_container(
                    api=api,
                    token="token",
                    account_id="account-1",
                    post_platform=target,
                )

        outcome = raised.exception
        self.assertTrue(outcome.ambiguous_media_publish)
        self.assertIn("outcome could not be confirmed", str(outcome))
        self.assertIn("provider_code=4", str(outcome))
        self.assertIn("error_subcode=2207051", str(outcome))
        self.assertIn("http_status=403", str(outcome))
        self.assertIn("fbtrace_id=trace-2207051", str(outcome))
        self.assertNotIn("must-not-appear", str(outcome))
        self.assertEqual(api.graph_post.call_count, 1)
        log_output = "\n".join(logs.output)
        self.assertIn("x-app-usage", log_output)
        self.assertIn("call_count", log_output)
        self.assertNotIn("must-not-appear", log_output)

    def test_unrelated_instagram_media_publish_error_is_unchanged(self):
        api = SimpleNamespace(
            graph_get=MagicMock(return_value={"status_code": "FINISHED"}),
            graph_post=MagicMock(side_effect=InstagramAPIError(
                "Instagram permission denied.",
                status_code=400,
                error_payload={"error": {"code": 10}},
            )),
        )
        target = SimpleNamespace(id="target-1", provider_container_id="container-1")

        with self.assertRaises(InstagramAPIError):
            MetaPublisher._publish_instagram_container(
                api=api,
                token="token",
                account_id="account-1",
                post_platform=target,
            )

    def test_instagram_container_error_includes_provider_status_without_publishing(self):
        api = SimpleNamespace(
            graph_get=MagicMock(return_value={
                "status_code": "ERROR",
                "status": "Media fetch failed.",
            }),
            graph_post=MagicMock(),
        )
        target = SimpleNamespace(provider_container_id="container-1")

        with self.assertRaisesMessage(
            ProviderPublishingError,
            "Instagram media container is error: Media fetch failed.",
        ):
            MetaPublisher._publish_instagram_container(
                api=api,
                token="token",
                account_id="account-1",
                post_platform=target,
            )

        api.graph_post.assert_not_called()

    def test_instagram_container_status_log_is_allowlisted(self):
        api = SimpleNamespace(
            last_response_status_code=200,
            graph_get=MagicMock(return_value={
                "status_code": "ERROR",
                "status": "Media fetch failed.",
                "error": {
                    "message": "Provider diagnostic.",
                    "code": 190,
                    "error_subcode": 463,
                    "type": "OAuthException",
                    "fbtrace_id": "trace-1",
                },
                "access_token": "must-not-be-logged",
                "unexpected_payload": "must-not-be-logged",
            }),
            graph_post=MagicMock(),
        )
        target = SimpleNamespace(id="target-1", provider_container_id="container-1")

        with self.assertLogs("apps.posts.publishing.meta", level="INFO") as logs:
            with self.assertRaises(ProviderPublishingError):
                MetaPublisher._publish_instagram_container(
                    api=api,
                    token="token",
                    account_id="account-1",
                    post_platform=target,
                )

        log_output = "\n".join(logs.output)
        self.assertIn("target_id=target-1", log_output)
        self.assertIn("container_id=container-1", log_output)
        self.assertIn("http_status=200", log_output)
        self.assertIn("message=Provider diagnostic.", log_output)
        self.assertIn("code=190", log_output)
        self.assertNotIn("must-not-be-logged", log_output)

    def test_instagram_container_error_without_status_keeps_generic_message(self):
        api = SimpleNamespace(
            graph_get=MagicMock(return_value={"status_code": "ERROR"}),
            graph_post=MagicMock(),
        )
        target = SimpleNamespace(provider_container_id="container-1")

        with self.assertRaisesMessage(
            ProviderPublishingError,
            "Instagram media container is error.",
        ):
            MetaPublisher._publish_instagram_container(
                api=api,
                token="token",
                account_id="account-1",
                post_platform=target,
            )

        api.graph_post.assert_not_called()

    def test_instagram_container_expired_does_not_retry_or_publish(self):
        api = SimpleNamespace(
            graph_get=MagicMock(return_value={"status_code": "EXPIRED"}),
            graph_post=MagicMock(),
        )
        target = SimpleNamespace(provider_container_id="container-1")

        with self.assertRaises(ProviderPublishingError):
            MetaPublisher._publish_instagram_container(
                api=api,
                token="token",
                account_id="account-1",
                post_platform=target,
            )

        api.graph_post.assert_not_called()

    def test_instagram_container_unknown_or_missing_status_fails_safely(self):
        for state in ({"status_code": "UNEXPECTED"}, {}):
            with self.subTest(state=state):
                api = SimpleNamespace(
                    graph_get=MagicMock(return_value=state),
                    graph_post=MagicMock(),
                )
                target = SimpleNamespace(provider_container_id="container-1")

                with self.assertRaises(ProviderPublishingError):
                    MetaPublisher._publish_instagram_container(
                        api=api,
                        token="token",
                        account_id="account-1",
                        post_platform=target,
                    )

                api.graph_post.assert_not_called()

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

    @patch("apps.posts.publishing.meta.InstagramAPIClient")
    @patch("apps.posts.publishing.meta.decrypt_instagram_token")
    @patch("apps.posts.publishing.meta.get_active_instagram_credential")
    def test_instagram_rate_limit_is_retryable_and_preserves_existing_container(
        self,
        get_credential,
        decrypt_token,
        client_class,
    ):
        account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="instagram-rate-limit",
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
            status=PostStatus.PUBLISHING,
            provider_container_id="existing-container",
            provider_state={"resume": "safe"},
        )
        get_credential.return_value = SimpleNamespace(
            encrypted_access_token="encrypted-token",
        )
        decrypt_token.return_value = "access-token"
        client_class.return_value.graph_get.side_effect = InstagramAPIError(
            "Instagram rate limited the request.",
            error_payload={"error": {"code": 4}},
        )

        with self.assertRaises(MediaProcessingPending) as raised:
            MetaPublisher().publish_instagram(post_platform=target)

        target.refresh_from_db()
        self.assertTrue(raised.exception.rate_limited)
        self.assertEqual(target.provider_container_id, "existing-container")
        self.assertEqual(target.provider_state, {"resume": "safe"})
        client_class.return_value.graph_post.assert_not_called()

    @patch("apps.posts.publishing.meta.InstagramAPIClient")
    @patch("apps.posts.publishing.meta.decrypt_instagram_token")
    @patch("apps.posts.publishing.meta.get_active_instagram_credential")
    def test_unrelated_code_four_instagram_error_is_not_retryable(
        self,
        get_credential,
        decrypt_token,
        client_class,
    ):
        account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="instagram-permission-error",
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
            status=PostStatus.PUBLISHING,
            provider_container_id="existing-container",
        )
        get_credential.return_value = SimpleNamespace(
            encrypted_access_token="encrypted-token",
        )
        decrypt_token.return_value = "access-token"
        client_class.return_value.graph_get.side_effect = InstagramAPIError(
            "Instagram permission denied.",
            error_payload={"error": {"code": 4}},
        )
        with self.assertRaises(InstagramAPIError):
            MetaPublisher().publish_instagram(post_platform=target)

    def test_instagram_rate_limit_backoff_is_bounded(self):
        pending = MediaProcessingPending("rate limited", rate_limited=True)
        normal = MediaProcessingPending("processing")

        self.assertEqual(_pending_retry_countdown(pending, 0), 60)
        self.assertEqual(_pending_retry_countdown(pending, 1), 120)
        self.assertEqual(_pending_retry_countdown(pending, 100), 15 * 60)
        self.assertEqual(_pending_retry_countdown(normal, 10), 30)

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

    def test_calendar_events_project_target_statuses_dates_and_media(self):
        scheduled_at = timezone.now() + timedelta(days=2)
        scheduled = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            publish_type=PostPublishType.SCHEDULE,
            status=PostStatus.SCHEDULED,
            scheduled_at=scheduled_at,
            timezone="Asia/Kolkata",
            caption="Scheduled calendar post",
        )
        scheduled_target = PostPlatform.objects.create(
            post=scheduled,
            platform=SocialPlatform.FACEBOOK,
            social_account=self.account,
            content_type="POST",
        )
        PostMedia.objects.create(
            post=scheduled,
            media_type="IMAGE",
            file="posts/calendar-image.jpg",
            mime_type="image/jpeg",
        )
        published = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            status=PostStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        published_target = PostPlatform.objects.create(
            post=published,
            platform=SocialPlatform.FACEBOOK,
            social_account=self.account,
            content_type="POST",
            status=PostStatus.PUBLISHED,
            published_at=published.published_at,
        )
        failed = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            status=PostStatus.FAILED,
            caption="Failed calendar post",
        )
        failed_target = PostPlatform.objects.create(
            post=failed,
            platform=SocialPlatform.FACEBOOK,
            social_account=self.account,
            content_type="STORY",
            status=PostStatus.FAILED,
            error_message="Provider rejected the post.",
        )

        response = self.api_client.get(
            "/api/posts/calendar/events/",
            {"month": scheduled_at.strftime("%Y-%m")},
        )

        self.assertEqual(response.status_code, 200)
        events = {event["id"]: event for event in response.json()["data"]}
        self.assertEqual(events[str(scheduled_target.id)]["status"], "SCHEDULED")
        self.assertEqual(
            events[str(scheduled_target.id)]["date"],
            scheduled_at.astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat(),
        )
        self.assertEqual(events[str(scheduled_target.id)]["media"][0]["type"], "IMAGE")
        self.assertNotIn(str(published_target.id), events)
        self.assertNotIn(str(failed_target.id), events)

    def test_calendar_events_filter_owned_targets_and_search(self):
        other_user = User.objects.create_user(
            email="other@example.com", first_name="Other", password="password"
        )
        other_organization = Organization.objects.create(
            organization_id="ORG-POST-OTHER",
            name="Other Organization",
            slug="other-organization",
            industry="Retail",
            created_by=other_user,
        )
        other_account = SocialAccount.objects.create(
            organization=other_organization,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id="other-page",
            account_name="Other Page",
        )
        own_post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            status=PostStatus.DRAFT,
            caption="Find this calendar post",
        )
        own_target = PostPlatform.objects.create(
            post=own_post,
            platform=SocialPlatform.FACEBOOK,
            social_account=self.account,
            content_type="POST",
        )
        other_post = Post.objects.create(
            organization=other_organization,
            created_by=other_user,
            status=PostStatus.DRAFT,
            caption="Private calendar post",
        )
        PostPlatform.objects.create(
            post=other_post,
            platform=SocialPlatform.FACEBOOK,
            social_account=other_account,
            content_type="POST",
        )

        response = self.api_client.get(
            "/api/posts/calendar/events/",
            {"search": "find this", "status": "DRAFT"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [event["id"] for event in response.json()["data"]],
            [str(own_target.id)],
        )

    def test_calendar_event_detail_returns_owned_target_in_calendar_event_shape(self):
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            status=PostStatus.DRAFT,
            caption="Calendar target detail",
        )
        target = PostPlatform.objects.create(
            post=post,
            platform=SocialPlatform.FACEBOOK,
            social_account=self.account,
            content_type="POST",
        )

        list_response = self.api_client.get("/api/posts/calendar/events/")
        detail_response = self.api_client.get(
            f"/api/posts/calendar/events/{target.id}/",
        )

        self.assertEqual(detail_response.status_code, 200)
        list_event = next(
            event
            for event in list_response.json()["data"]
            if event["id"] == str(target.id)
        )
        self.assertEqual(detail_response.json()["data"], list_event)

    def test_calendar_event_detail_returns_not_found_for_another_users_target(self):
        other_user = User.objects.create_user(
            email="calendar-detail-other@example.com",
            first_name="Other",
            password="password",
        )
        other_organization = Organization.objects.create(
            organization_id="ORG-CALENDAR-DETAIL-OTHER",
            name="Other Organization",
            slug="calendar-detail-other",
            industry="Retail",
            created_by=other_user,
        )
        other_account = SocialAccount.objects.create(
            organization=other_organization,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id="calendar-detail-other-page",
            account_name="Other Page",
        )
        other_post = Post.objects.create(
            organization=other_organization,
            created_by=other_user,
            status=PostStatus.DRAFT,
        )
        other_target = PostPlatform.objects.create(
            post=other_post,
            platform=SocialPlatform.FACEBOOK,
            social_account=other_account,
            content_type="POST",
        )

        response = self.api_client.get(
            f"/api/posts/calendar/events/{other_target.id}/",
        )

        self.assertEqual(response.status_code, 404)

    def test_calendar_filters_return_owned_organizations_and_connected_accounts(self):
        connected = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.INSTAGRAM,
            platform_account_id="instagram-calendar",
            account_name="Calendar Instagram",
            status=SocialAccountStatus.CONNECTED,
            is_valid=True,
        )
        response = self.api_client.get("/api/posts/calendar/filters/")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertIn(
            {"value": self.organization.organization_id, "label": self.organization.name},
            data["organizations"],
        )
        self.assertIn(str(connected.id), [item["value"] for item in data["social_accounts"]])
        self.assertNotIn(str(self.account.id), [item["value"] for item in data["social_accounts"]])


class PostActivityServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="post-activity-owner@example.com",
            first_name="Post Activity",
            password="password",
        )
        self.organization = Organization.objects.create(
            organization_id="ORG-POST-ACTIVITY",
            name="Post Activity Organization",
            slug="post-activity-organization",
            industry="Retail",
            created_by=self.user,
        )
        self.account = SocialAccount.objects.create(
            organization=self.organization,
            platform=SocialPlatform.FACEBOOK,
            platform_account_id="post-activity-page",
            account_name="Post Activity Page",
        )

    def create_draft_post(self):
        post = Post.objects.create(
            organization=self.organization,
            created_by=self.user,
            publish_type=PostPublishType.DRAFT,
            status=PostStatus.DRAFT,
        )
        target = PostPlatform.objects.create(
            post=post,
            social_account=self.account,
            platform=SocialPlatform.FACEBOOK,
            content_type="POST",
            status=PostStatus.DRAFT,
        )
        return post, target

    def test_post_creation_records_user_activity(self):
        post = create_post(
            organization=self.organization,
            created_by=self.user,
            validated_data={
                "targets": [{"social_account": self.account.id, "content_type": "POST"}],
                "media": [],
                "caption": "Activity draft",
                "publish_type": PostPublishType.DRAFT,
                "timezone": "Asia/Kolkata",
            },
        )

        self.assertTrue(
            ActivityLog.objects.filter(
                organization=self.organization,
                post=post,
                event_type=ActivityEventType.POST_CREATED,
                source=ActivitySource.USER,
                actor=self.user,
            ).exists()
        )
        self.assertFalse(
            ActivityLog.objects.filter(
                post=post,
                event_type=ActivityEventType.POST_SCHEDULED,
            ).exists()
        )

    @patch("apps.posts.services.validate_target_accounts")
    def test_scheduled_creation_records_one_aggregate_schedule_activity(self, _validate_targets):
        future = timezone.localtime(timezone.now() + timedelta(hours=1))

        post = create_post(
            organization=self.organization,
            created_by=self.user,
            validated_data={
                "targets": [{"social_account": self.account.id, "content_type": "POST"}],
                "media": [],
                "caption": "Activity scheduled post",
                "publish_type": PostPublishType.SCHEDULE,
                "publish_date": future.date(),
                "publish_time": future.time(),
                "timezone": "Asia/Kolkata",
            },
        )

        schedules = ActivityLog.objects.filter(
            post=post,
            event_type=ActivityEventType.POST_SCHEDULED,
        )
        self.assertEqual(schedules.count(), 1)
        schedule = schedules.get()
        self.assertIsNone(schedule.post_platform)
        self.assertEqual(schedule.metadata["schedule_scope"], "POST")
        self.assertEqual(schedule.source, ActivitySource.USER)
        self.assertEqual(schedule.actor, self.user)

    @patch("apps.posts.services.validate_target_accounts")
    def test_post_scheduling_records_one_retry_safe_aggregate_activity(self, _validate_targets):
        post, _target = self.create_draft_post()
        future = timezone.localtime(timezone.now() + timedelta(hours=2))

        schedule_post(
            post_id=post.id,
            organization_id=self.organization.id,
            publish_date=future.date(),
            publish_time=future.time(),
            timezone_name="Asia/Kolkata",
            actor=self.user,
        )
        schedule_post(
            post_id=post.id,
            organization_id=self.organization.id,
            publish_date=future.date(),
            publish_time=future.time(),
            timezone_name="Asia/Kolkata",
            reschedule=True,
            actor=self.user,
        )

        schedules = ActivityLog.objects.filter(
            post=post,
            event_type=ActivityEventType.POST_SCHEDULED,
        )
        self.assertEqual(schedules.count(), 1)
        schedule = schedules.get()
        self.assertIsNone(schedule.post_platform)
        self.assertTrue(schedule.idempotency_key)
        self.assertEqual(schedule.metadata["schedule_scope"], "POST")

    @patch("apps.posts.services.validate_target_accounts")
    def test_target_scheduling_records_one_retry_safe_target_activity(self, _validate_targets):
        post, target = self.create_draft_post()
        future = timezone.localtime(timezone.now() + timedelta(hours=3))

        schedule_post_target(
            post_id=post.id,
            organization_id=self.organization.id,
            target_id=target.id,
            publish_date=future.date(),
            publish_time=future.time(),
            timezone_name="Asia/Kolkata",
            actor=self.user,
        )
        schedule_post_target(
            post_id=post.id,
            organization_id=self.organization.id,
            target_id=target.id,
            publish_date=future.date(),
            publish_time=future.time(),
            timezone_name="Asia/Kolkata",
            actor=self.user,
        )

        schedules = ActivityLog.objects.filter(
            post=post,
            event_type=ActivityEventType.POST_SCHEDULED,
        )
        self.assertEqual(schedules.count(), 1)
        schedule = schedules.get()
        self.assertEqual(schedule.post_platform, target)
        self.assertEqual(schedule.metadata["schedule_scope"], "POST_PLATFORM")
        self.assertEqual(schedule.source, ActivitySource.USER)
        self.assertEqual(schedule.actor, self.user)
