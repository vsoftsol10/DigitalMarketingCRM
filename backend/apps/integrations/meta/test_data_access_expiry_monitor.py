from contextlib import contextmanager, nullcontext, ExitStack
from datetime import datetime, timedelta, timezone as datetime_timezone
from itertools import cycle
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.db import OperationalError
from django.test import SimpleTestCase, override_settings
from apps.integrations.meta.lifecycle import MetaTokenLifecycleService
from apps.integrations.meta.models import MetaAccountCredential, MetaCredentialType
from apps.notifications.models import UserNotification, UserNotificationType
from apps.notifications.services import (
    meta_user_data_access_expiry_event_key,
)
from apps.social_accounts.models import (
    SocialAccount,
    SocialConnection,
    SocialConnectionStatus,
)


@contextmanager
def mocked_monitor_database(connection_specs, *, candidate_rows=None):
    """Mock the monitor's ORM reads while preserving its query/control flow."""
    if candidate_rows is None:
        candidate_rows = [
            {
                "social_connection_id": str(spec["connection"].pk),
                "social_connection__organization_id": spec[
                    "connection"
                ].organization.pk,
            }
            for spec in connection_specs
        ]

    candidate_queryset = MagicMock()
    candidate_queryset.order_by.return_value.values.return_value.iterator.side_effect = (
        lambda **kwargs: iter(candidate_rows)
    )

    warning_queryset = MagicMock()
    warning_queryset.values.return_value.iterator.side_effect = (
        lambda **kwargs: iter([])
    )

    connection_lock_querysets = []
    credential_lock_querysets = []
    for spec in connection_specs:
        connection_queryset = MagicMock()
        connection_queryset.select_related.return_value.filter.return_value.first.return_value = (
            spec["connection"]
        )
        connection_lock_querysets.append(connection_queryset)

        credential_queryset = MagicMock()
        credential_queryset.order_by.return_value.values.return_value.first.return_value = {
            "data_access_expires_at": spec.get("expires_at")
        }
        credential_lock_queryset = MagicMock()
        credential_lock_queryset.filter.return_value = credential_queryset
        credential_lock_querysets.append(credential_lock_queryset)

    with ExitStack() as stack:
        candidate_filter = stack.enter_context(
            patch.object(
                MetaAccountCredential.objects,
                "filter",
                return_value=candidate_queryset,
            )
        )
        stack.enter_context(
            patch.object(
                MetaAccountCredential.objects,
                "select_for_update",
                side_effect=cycle(credential_lock_querysets),
            )
        )
        connection_lock = stack.enter_context(
            patch.object(
                SocialConnection.objects,
                "select_for_update",
                side_effect=cycle(connection_lock_querysets),
            )
        )
        stack.enter_context(
            patch.object(
                UserNotification.objects,
                "filter",
                return_value=warning_queryset,
            )
        )
        stack.enter_context(
            patch(
                "apps.integrations.meta.lifecycle.transaction.atomic",
                return_value=nullcontext(),
            )
        )
        yield {
            "candidate_queryset": candidate_queryset,
            "candidate_filter": candidate_filter,
            "warning_queryset": warning_queryset,
            "connection_lock": connection_lock,
            "connection_lock_querysets": connection_lock_querysets,
            "credential_lock_querysets": credential_lock_querysets,
        }


class MetaUserDataAccessExpiryPolicyTests(SimpleTestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 13, 12, 0, tzinfo=datetime_timezone.utc)
        self.organization = SimpleNamespace(
            pk="organization-1",
            name="Example Organization",
            created_by_id=12,
        )
        self.connection = SimpleNamespace(
            pk="connection-1",
            organization=self.organization,
        )

    def test_14_day_warning_is_recorded(self):
        with (
            patch(
                "apps.notifications.services.record_meta_user_data_access_expiry_warning"
            ) as record_warning,
            patch(
                "apps.notifications.services.resolve_meta_user_data_access_expiry_warnings"
            ) as resolve_warning,
        ):
            result = MetaTokenLifecycleService._apply_user_data_access_expiry_policy(
                MetaTokenLifecycleService.__new__(MetaTokenLifecycleService),
                connection=self.connection,
                expires_at=self.now + timedelta(days=14),
                now=self.now,
            )

        self.assertEqual(result, "warning")
        record_warning.assert_called_once_with(
            organization=self.organization,
            connection_id=self.connection.pk,
            stage="14d",
            expires_at=self.now + timedelta(days=14),
        )
        resolve_warning.assert_called_once_with(
            connection_id=self.connection.pk,
            organization=self.organization,
            stage="3d",
        )

    def test_3_day_warning_escalates_and_resolves_14_day_warning(self):
        with (
            patch(
                "apps.notifications.services.record_meta_user_data_access_expiry_warning"
            ) as record_warning,
            patch(
                "apps.notifications.services.resolve_meta_user_data_access_expiry_warnings"
            ) as resolve_warning,
        ):
            result = MetaTokenLifecycleService._apply_user_data_access_expiry_policy(
                MetaTokenLifecycleService.__new__(MetaTokenLifecycleService),
                connection=self.connection,
                expires_at=self.now + timedelta(days=3),
                now=self.now,
            )

        self.assertEqual(result, "urgent")
        record_warning.assert_called_once_with(
            organization=self.organization,
            connection_id=self.connection.pk,
            stage="3d",
            expires_at=self.now + timedelta(days=3),
        )
        resolve_warning.assert_called_once_with(
            connection_id=self.connection.pk,
            organization=self.organization,
            stage="14d",
        )

    def test_expired_expiry_uses_reconnect_notification_without_status_change(self):
        credential = SimpleNamespace(status="ACTIVE")
        with (
            patch(
                "apps.notifications.services.record_social_credential_reconnect_required"
            ) as record_reconnect,
            patch(
                "apps.notifications.services.record_meta_user_data_access_expiry_warning"
            ) as record_warning,
            patch(
                "apps.notifications.services.resolve_meta_user_data_access_expiry_warnings"
            ) as resolve_warning,
        ):
            result = MetaTokenLifecycleService._apply_user_data_access_expiry_policy(
                MetaTokenLifecycleService.__new__(MetaTokenLifecycleService),
                connection=self.connection,
                expires_at=self.now,
                now=self.now,
            )

        self.assertEqual(result, "expired")
        self.assertEqual(credential.status, "ACTIVE")
        record_reconnect.assert_called_once_with(
            organization=self.organization,
            scope="meta-connection",
            subject_id=self.connection.pk,
            platform="facebook",
        )
        record_warning.assert_not_called()
        resolve_warning.assert_called_once_with(
            connection_id=self.connection.pk,
            organization=self.organization,
        )

    def test_missing_or_distant_expiry_resolves_stale_warnings(self):
        service = MetaTokenLifecycleService.__new__(MetaTokenLifecycleService)
        with (
            patch(
                "apps.notifications.services.record_meta_user_data_access_expiry_warning"
            ) as record_warning,
            patch(
                "apps.notifications.services.resolve_meta_user_data_access_expiry_warnings"
            ) as resolve_warning,
        ):
            missing_result = service._apply_user_data_access_expiry_policy(
                connection=self.connection,
                expires_at=None,
                now=self.now,
            )
            distant_result = service._apply_user_data_access_expiry_policy(
                connection=self.connection,
                expires_at=self.now + timedelta(days=20),
                now=self.now,
            )

        self.assertEqual(missing_result, "missing_expiry")
        self.assertEqual(distant_result, "resolved")
        self.assertEqual(resolve_warning.call_count, 2)
        record_warning.assert_not_called()

    def test_naive_expiry_is_normalized_and_already_expired_never_warns(self):
        naive_now = datetime(2026, 11, 13, 12, 0)
        self.assertEqual(
            MetaTokenLifecycleService._data_access_warning_stage(
                naive_now - timedelta(seconds=1),
                now=naive_now.replace(tzinfo=datetime_timezone.utc),
            ),
            "expired",
        )

    def test_warning_event_keys_are_stable_and_stage_specific(self):
        warning_key = meta_user_data_access_expiry_event_key(
            connection_id=self.connection.pk,
            stage="14d",
        )
        urgent_key = meta_user_data_access_expiry_event_key(
            connection_id=self.connection.pk,
            stage="3d",
        )
        self.assertEqual(warning_key, "meta-user-data-access-expiry:connection-1:14d")
        self.assertEqual(urgent_key, "meta-user-data-access-expiry:connection-1:3d")
        self.assertNotEqual(warning_key, urgent_key)

    def test_duplicate_recording_reuses_existing_unresolved_notification(self):
        notification = SimpleNamespace(resolved_at=None)
        queryset = MagicMock()
        queryset.first.return_value = notification
        with (
            patch("apps.notifications.services.transaction.atomic", return_value=nullcontext()),
            patch.object(UserNotification.objects, "filter", return_value=queryset),
            patch("apps.notifications.services._record_user_notification") as create,
        ):
            from apps.notifications.services import record_meta_user_data_access_expiry_warning

            first = record_meta_user_data_access_expiry_warning(
                organization=self.organization,
                connection_id=self.connection.pk,
                stage="14d",
                expires_at=self.now + timedelta(days=14),
            )
            second = record_meta_user_data_access_expiry_warning(
                organization=self.organization,
                connection_id=self.connection.pk,
                stage="14d",
                expires_at=self.now + timedelta(days=14),
            )

        self.assertIs(first, notification)
        self.assertIs(second, notification)
        create.assert_not_called()
        self.assertIn(
            "unique_active_user_notification_key",
            {constraint.name for constraint in UserNotification._meta.constraints},
        )

    def test_successful_user_credential_save_resolves_expiry_warnings(self):
        from apps.integrations.meta.services import MetaSocialAccountService

        connection = SimpleNamespace(
            pk="connection-1",
            organization=self.organization,
        )
        existing_credential = SimpleNamespace(
            social_account=None,
            access_token="encrypted-old",
            token_expires_at=None,
            status="ACTIVE",
            last_verified_at=None,
            is_deleted=False,
            deleted_at=None,
            pk="credential-1",
            save=MagicMock(),
        )
        queryset = MagicMock()
        queryset.order_by.return_value.first.return_value = existing_credential
        service = MetaSocialAccountService(organization=self.organization, user=None)
        with (
            patch.object(MetaAccountCredential.objects, "filter", return_value=queryset),
            patch("apps.integrations.meta.services.encrypt_token", return_value="encrypted-new"),
            patch("apps.integrations.meta.services.transaction.on_commit"),
            patch("apps.notifications.services.resolve_social_credential_reconnect_required"),
            patch(
                "apps.notifications.services.resolve_meta_user_data_access_expiry_warnings"
            ) as resolve_warning,
            patch.object(MetaSocialAccountService, "_schedule_user_credential_health_check"),
        ):
            service._save_user_credential(
                connection=connection,
                user_access_token="raw-token-is-only-a-test-fixture",
                token_expires_at=None,
            )

        resolve_warning.assert_called_once_with(
            organization=self.organization,
            connection_id=connection.pk,
        )


class MetaUserDataAccessExpiryMonitorTaskTests(SimpleTestCase):
    def test_monitor_task_is_scheduled_every_six_hours(self):
        from django.conf import settings

        schedule = settings.CELERY_BEAT_SCHEDULE[
            "monitor-meta-user-data-access-expiry"
        ]
        self.assertEqual(schedule["schedule"], 6 * 60 * 60.0)
        self.assertEqual(
            schedule["task"],
            "apps.integrations.meta.tasks.monitor_meta_user_data_access_expiry_task",
        )

    def test_monitor_locks_connection_and_reads_credentials_without_pages_or_api_calls(self):
        org_id = "organization-1"
        connection_id = "connection-1"
        organization = SimpleNamespace(pk=org_id, name="Example", created_by_id=1)
        connection = SimpleNamespace(pk=connection_id, organization=organization)

        candidate_queryset = MagicMock()
        candidate_queryset.order_by.return_value.values.return_value.iterator.return_value = iter(
            [
                {
                    "social_connection_id": connection_id,
                    "social_connection__organization_id": org_id,
                }
            ]
        )
        credential_queryset = MagicMock()
        credential_queryset.order_by.return_value.values.return_value.first.return_value = {
            "data_access_expires_at": None
        }
        warning_queryset = MagicMock()
        warning_queryset.values.return_value.iterator.return_value = iter([])
        connection_queryset = MagicMock()
        connection_queryset.select_related.return_value.filter.return_value.first.return_value = connection
        credential_lock_queryset = MagicMock()
        credential_lock_queryset.filter.return_value = credential_queryset

        api = MagicMock()
        service = MetaTokenLifecycleService(api_client=api)
        with (
            patch.object(
                MetaAccountCredential.objects,
                "filter",
                side_effect=[candidate_queryset, credential_queryset],
            ) as credential_filter,
            patch.object(
                SocialConnection.objects,
                "select_for_update",
                return_value=connection_queryset,
            ) as select_connection_for_update,
            patch.object(
                MetaAccountCredential.objects,
                "select_for_update",
                return_value=credential_lock_queryset,
            ),
            patch.object(UserNotification.objects, "filter", return_value=warning_queryset),
            patch("apps.integrations.meta.lifecycle.transaction.atomic", return_value=nullcontext()),
            patch(
                "apps.notifications.services.record_meta_user_data_access_expiry_warning"
            ) as record_warning,
            patch(
                "apps.notifications.services.resolve_meta_user_data_access_expiry_warnings"
            ) as resolve_warning,
            patch.object(SocialAccount.objects, "filter") as page_filter,
        ):
            result = service.monitor_user_data_access_expiry(
                now=datetime(2026, 11, 13, 12, 0, tzinfo=datetime_timezone.utc)
            )

        self.assertEqual(result["checked"], 1)
        self.assertEqual(result["missing_expiry"], 1)
        self.assertTrue(select_connection_for_update.called)
        candidate_filters = [entry.kwargs for entry in credential_filter.call_args_list]
        self.assertEqual(candidate_filters[0]["credential_type"], MetaCredentialType.USER)
        self.assertEqual(candidate_filters[0]["status"], "ACTIVE")
        self.assertFalse(candidate_filters[0]["is_deleted"])
        self.assertEqual(
            candidate_filters[0]["social_connection__status"],
            SocialConnectionStatus.ACTIVE,
        )
        self.assertFalse(candidate_filters[0]["social_connection__is_deleted"])
        self.assertNotIn("social_account", candidate_filters[0])
        candidate_queryset.order_by.return_value.values.assert_called_once_with(
            "social_connection_id",
            "social_connection__organization_id",
        )
        selected_filter = credential_lock_queryset.filter.call_args.kwargs
        self.assertEqual(selected_filter["credential_type"], MetaCredentialType.USER)
        self.assertEqual(selected_filter["status"], "ACTIVE")
        self.assertFalse(selected_filter["is_deleted"])
        self.assertNotIn("social_account", selected_filter)
        credential_queryset.order_by.return_value.values.assert_called_once_with(
            "data_access_expires_at"
        )
        self.assertNotIn(
            "access_token",
            credential_queryset.order_by.return_value.values.call_args.args,
        )
        self.assertTrue(select_connection_for_update.called)
        page_filter.assert_not_called()
        record_warning.assert_not_called()
        resolve_warning.assert_called_once_with(
            connection_id=connection_id,
            organization=organization,
        )
        api.diagnose_token.assert_not_called()
        api.get_user_permissions.assert_not_called()

    def test_monitor_processes_multiple_user_connections_independently(self):
        now = datetime(2026, 11, 13, 12, 0, tzinfo=datetime_timezone.utc)
        connections = [
            SimpleNamespace(
                pk="connection-1",
                organization=SimpleNamespace(
                    pk="organization-1",
                    name="Organization One",
                    created_by_id=1,
                ),
            ),
            SimpleNamespace(
                pk="connection-2",
                organization=SimpleNamespace(
                    pk="organization-2",
                    name="Organization Two",
                    created_by_id=2,
                ),
            ),
        ]
        specs = [
            {"connection": connections[0], "expires_at": now + timedelta(days=14)},
            {"connection": connections[1], "expires_at": now + timedelta(days=3)},
        ]
        service = MetaTokenLifecycleService(api_client=MagicMock())
        processed_connections = []

        with (
            mocked_monitor_database(specs),
            patch.object(
                service,
                "_apply_user_data_access_expiry_policy",
                side_effect=lambda *, connection, **kwargs: (
                    processed_connections.append(connection.pk) or "warning"
                ),
            ),
        ):
            result = service.monitor_user_data_access_expiry(now=now)

        self.assertEqual(result["checked"], 2)
        self.assertEqual(result["warning"], 2)
        self.assertEqual(processed_connections, ["connection-1", "connection-2"])

    def test_repeated_rows_for_shared_connection_are_processed_once(self):
        now = datetime(2026, 11, 13, 12, 0, tzinfo=datetime_timezone.utc)
        organization = SimpleNamespace(
            pk="organization-1",
            name="Example Organization",
            created_by_id=12,
        )
        connection = SimpleNamespace(pk="connection-1", organization=organization)
        spec = {"connection": connection, "expires_at": now + timedelta(days=14)}
        repeated_candidate = {
            "social_connection_id": connection.pk,
            "social_connection__organization_id": organization.pk,
        }
        service = MetaTokenLifecycleService(api_client=MagicMock())
        synthetic_pages = [
            SimpleNamespace(connection_id=connection.pk, platform="facebook"),
            SimpleNamespace(connection_id=connection.pk, platform="facebook"),
        ]
        self.assertEqual(
            {page.connection_id for page in synthetic_pages},
            {connection.pk},
        )

        with (
            mocked_monitor_database(
                [spec],
                candidate_rows=[repeated_candidate, repeated_candidate],
            ),
            patch.object(
                SocialAccount.objects,
                "filter",
            ) as page_filter,
            patch(
                "apps.notifications.services.record_meta_user_data_access_expiry_warning"
            ) as record_warning,
            patch(
                "apps.notifications.services.resolve_meta_user_data_access_expiry_warnings"
            ),
        ):
            result = service.monitor_user_data_access_expiry(now=now)

        self.assertEqual(result["checked"], 1)
        record_warning.assert_called_once_with(
            organization=organization,
            connection_id=connection.pk,
            stage="14d",
            expires_at=spec["expires_at"],
        )
        page_filter.assert_not_called()

    def test_user_connection_without_active_pages_is_still_monitored(self):
        now = datetime(2026, 11, 13, 12, 0, tzinfo=datetime_timezone.utc)
        organization = SimpleNamespace(
            pk="organization-no-pages",
            name="Organization Without Pages",
            created_by_id=12,
        )
        connection = SimpleNamespace(
            pk="connection-without-pages",
            organization=organization,
        )
        spec = {"connection": connection, "expires_at": now + timedelta(days=14)}
        service = MetaTokenLifecycleService(api_client=MagicMock())

        with (
            mocked_monitor_database([spec]),
            patch.object(SocialAccount.objects, "filter") as page_filter,
            patch.object(
                service,
                "_apply_user_data_access_expiry_policy",
                return_value="warning",
            ) as apply_policy,
        ):
            result = service.monitor_user_data_access_expiry(now=now)

        self.assertEqual(result["checked"], 1)
        apply_policy.assert_called_once()
        self.assertEqual(apply_policy.call_args.kwargs["connection"].pk, connection.pk)
        page_filter.assert_not_called()

    def test_inactive_or_deleted_user_credentials_are_filtered_out(self):
        service = MetaTokenLifecycleService(api_client=MagicMock())
        with mocked_monitor_database([]) as mocks:
            result = service.monitor_user_data_access_expiry(
                now=datetime(2026, 11, 13, 12, 0, tzinfo=datetime_timezone.utc)
            )

        self.assertEqual(result["checked"], 0)
        mocks["candidate_filter"].assert_called_once_with(
            credential_type=MetaCredentialType.USER,
            status="ACTIVE",
            is_deleted=False,
            social_connection__isnull=False,
            social_connection__provider="meta",
            social_connection__status=SocialConnectionStatus.ACTIVE,
            social_connection__is_deleted=False,
        )

    def test_stale_warning_is_resolved_for_deleted_or_disconnected_user_credential(self):
        candidate_queryset = MagicMock()
        candidate_queryset.order_by.return_value.values.return_value.iterator.return_value = iter([])
        warning_queryset = MagicMock()
        warning_queryset.values.return_value.iterator.return_value = iter(
            [
                {
                    "event_key": "meta-user-data-access-expiry:connection-1:14d",
                    "organization_id": "organization-1",
                }
            ]
        )
        service = MetaTokenLifecycleService(api_client=MagicMock())
        with (
            patch.object(MetaAccountCredential.objects, "filter", return_value=candidate_queryset),
            patch.object(UserNotification.objects, "filter", return_value=warning_queryset),
            patch(
                "apps.notifications.services.resolve_meta_user_data_access_expiry_warnings",
                return_value=1,
            ) as resolve,
        ):
            result = service.monitor_user_data_access_expiry(
                now=datetime(2026, 11, 13, 12, 0, tzinfo=datetime_timezone.utc)
            )

        self.assertEqual(result["checked"], 0)
        self.assertEqual(result["resolved"], 1)
        resolve.assert_called_once_with(
            connection_id="connection-1",
            organization_id="organization-1",
        )

    def test_repeated_monitor_execution_reuses_same_warning_key(self):
        now = datetime(2026, 11, 13, 12, 0, tzinfo=datetime_timezone.utc)
        organization = SimpleNamespace(
            pk="organization-repeat",
            name="Repeated Monitor Organization",
            created_by_id=1,
        )
        connection = SimpleNamespace(pk="connection-repeat", organization=organization)
        spec = {"connection": connection, "expires_at": now + timedelta(days=14)}
        service = MetaTokenLifecycleService(api_client=MagicMock())
        in_memory_active_notifications = {}

        def record_once_per_key(*, organization, connection_id, stage, expires_at):
            key = meta_user_data_access_expiry_event_key(
                connection_id=connection_id,
                stage=stage,
            )
            in_memory_active_notifications.setdefault(
                key,
                SimpleNamespace(resolved_at=None, organization=organization),
            )
            return in_memory_active_notifications[key]

        with (
            mocked_monitor_database([spec]),
            patch(
                "apps.notifications.services.record_meta_user_data_access_expiry_warning",
                side_effect=record_once_per_key,
            ) as record_warning,
            patch(
                "apps.notifications.services.resolve_meta_user_data_access_expiry_warnings"
            ),
        ):
            first = service.monitor_user_data_access_expiry(now=now)
            second = service.monitor_user_data_access_expiry(now=now)

        expected_key = meta_user_data_access_expiry_event_key(
            connection_id=connection.pk,
            stage="14d",
        )
        self.assertEqual(first["warning"], 1)
        self.assertEqual(second["warning"], 1)
        self.assertEqual(record_warning.call_count, 2)
        self.assertEqual(
            [call.kwargs["connection_id"] for call in record_warning.call_args_list],
            [connection.pk, connection.pk],
        )
        self.assertEqual(set(in_memory_active_notifications), {expected_key})

    def test_expired_monitor_uses_reconnect_required_notification(self):
        now = datetime(2026, 11, 13, 12, 0, tzinfo=datetime_timezone.utc)
        organization = SimpleNamespace(
            pk="organization-expired",
            name="Expired Connection Organization",
            created_by_id=1,
        )
        connection = SimpleNamespace(pk="connection-expired", organization=organization)
        spec = {"connection": connection, "expires_at": now - timedelta(seconds=1)}
        service = MetaTokenLifecycleService(api_client=MagicMock())

        with (
            mocked_monitor_database([spec]),
            patch(
                "apps.notifications.services.record_social_credential_reconnect_required"
            ) as record_reconnect,
            patch(
                "apps.notifications.services.record_meta_user_data_access_expiry_warning"
            ) as record_warning,
            patch(
                "apps.notifications.services.resolve_meta_user_data_access_expiry_warnings"
            ) as resolve_warning,
        ):
            result = service.monitor_user_data_access_expiry(now=now)

        self.assertEqual(result["expired"], 1)
        record_reconnect.assert_called_once_with(
            organization=organization,
            scope="meta-connection",
            subject_id=connection.pk,
            platform="facebook",
        )
        record_warning.assert_not_called()
        resolve_warning.assert_called_once_with(
            connection_id=connection.pk,
            organization=organization,
        )

    def test_database_error_for_one_connection_propagates_and_stops_iteration(self):
        now = datetime(2026, 11, 13, 12, 0, tzinfo=datetime_timezone.utc)
        connections = [
            SimpleNamespace(
                pk="connection-first",
                organization=SimpleNamespace(
                    pk="organization-first",
                    name="First Organization",
                    created_by_id=1,
                ),
            ),
            SimpleNamespace(
                pk="connection-second",
                organization=SimpleNamespace(
                    pk="organization-second",
                    name="Second Organization",
                    created_by_id=2,
                ),
            ),
        ]
        specs = [
            {"connection": connection, "expires_at": now + timedelta(days=20)}
            for connection in connections
        ]
        service = MetaTokenLifecycleService(api_client=MagicMock())
        processed_connections = []

        with mocked_monitor_database(specs) as mocks:
            mocks["connection_lock_querysets"][1].select_related.return_value.filter.return_value.first.side_effect = (
                OperationalError("synthetic database failure")
            )
            with patch.object(
                service,
                "_apply_user_data_access_expiry_policy",
                side_effect=lambda *, connection, **kwargs: (
                    processed_connections.append(connection.pk) or "resolved"
                ),
            ) as apply_policy:
                with self.assertRaises(OperationalError):
                    service.monitor_user_data_access_expiry(now=now)

        self.assertEqual(processed_connections, ["connection-first"])
        self.assertEqual(apply_policy.call_count, 1)

    def test_monitor_task_delegates_only_to_database_monitor(self):
        from apps.integrations.meta.tasks import monitor_meta_user_data_access_expiry_task

        with patch("apps.integrations.meta.tasks.MetaTokenLifecycleService") as lifecycle_class:
            lifecycle_class.return_value.monitor_user_data_access_expiry.return_value = {
                "checked": 0
            }
            result = monitor_meta_user_data_access_expiry_task.run()

        self.assertEqual(result, {"checked": 0})
        lifecycle = lifecycle_class.return_value
        lifecycle.monitor_user_data_access_expiry.assert_called_once_with()
        lifecycle.renew_due_user_credentials.assert_not_called()
        lifecycle.refresh_due_credentials.assert_not_called()

    def test_monitor_task_retains_celery_retry_configuration(self):
        from apps.integrations.meta.tasks import monitor_meta_user_data_access_expiry_task

        self.assertIn(Exception, monitor_meta_user_data_access_expiry_task.autoretry_for)
        self.assertEqual(monitor_meta_user_data_access_expiry_task.max_retries, 3)
        self.assertTrue(monitor_meta_user_data_access_expiry_task.retry_backoff)

    @override_settings(META_USER_TOKEN_AUTO_RENEWAL_ENABLED=False)
    def test_existing_hourly_task_still_runs_page_maintenance_without_renewal(self):
        from apps.integrations.meta.tasks import maintain_meta_tokens_task

        run = SimpleNamespace(save=MagicMock())
        service = MagicMock()
        service.refresh_due_credentials.return_value = {
            "checked": 1,
            "valid": 1,
            "retry": 0,
            "reconnect_needed": 0,
        }
        with (
            patch(
                "apps.integrations.meta.tasks.MetaTokenMaintenanceRun.objects.create",
                return_value=run,
            ),
            patch(
                "apps.integrations.meta.tasks.MetaTokenLifecycleService",
                return_value=service,
            ),
        ):
            result = maintain_meta_tokens_task.run()

        service.refresh_due_credentials.assert_called_once_with()
        service.renew_due_user_credentials.assert_not_called()
        self.assertFalse(result["user_renewal_enabled"])
