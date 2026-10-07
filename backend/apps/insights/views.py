from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.pagination import StandardResultsSetPagination
from apps.common.responses import success_response

from .selectors import get_accessible_organizations
from .serializers import (
    InsightsAccountSerializer,
    InsightsDateRangeQuerySerializer,
    InsightsOrganizationSerializer,
    InsightsResponseSerializer,
    InsightsSnapshotMediaSerializer,
    InsightsSnapshotQuerySerializer,
    InsightsSyncRequestSerializer,
)
from .services import (
    build_insights_response,
    get_selected_account,
    list_organization_accounts,
)
from .snapshot_read import (
    build_account_snapshot_read,
    build_content_snapshot_read,
    get_duration_slot_days,
    get_content_freshness,
)
from .models import InsightsSyncStatus
from .orchestration import request_account_insights_sync


class InsightsOrganizationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = InsightsOrganizationSerializer(
            get_accessible_organizations(user=request.user),
            many=True,
        ).data
        return success_response(
            data=data,
            message="Accessible Insights organizations fetched successfully.",
        )


class InsightsOrganizationAccountListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organization_id):
        accounts = list_organization_accounts(
            user=request.user,
            organization_id=organization_id,
            platform=request.query_params.get("platform"),
        )
        data = InsightsAccountSerializer(accounts, many=True).data
        return success_response(
            data=data,
            message="Connected Insights accounts fetched successfully.",
        )


class InsightsAccountDataAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organization_id, social_account_id):
        query = InsightsDateRangeQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        organization, account = get_selected_account(
            user=request.user,
            organization_id=organization_id,
            social_account_id=social_account_id,
        )
        payload = build_insights_response(
            organization=organization,
            account=account,
            since=query.validated_data.get("since"),
            until=query.validated_data.get("until"),
            cursor=query.validated_data.get("cursor"),
        )
        data = InsightsResponseSerializer(payload).data
        return success_response(
            data=data,
            message="Insights fetched for the selected account.",
        )


class InsightsAccountSnapshotAPIView(APIView):
    """Read the selected account's persisted snapshot without provider calls."""

    permission_classes = [IsAuthenticated]

    def get(self, request, organization_id, social_account_id):
        query = InsightsSnapshotQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        organization, account = get_selected_account(
            user=request.user,
            organization_id=organization_id,
            social_account_id=social_account_id,
        )
        if query.validated_data["platform"] != account.platform:
            raise ValidationError({"platform": "platform must match the selected account."})

        duration_days = get_duration_slot_days(
            account=account,
            since=query.validated_data["since"],
            until=query.validated_data["until"],
        )
        payload = build_account_snapshot_read(
            organization=organization,
            account=account,
            since=query.validated_data["since"],
            until=query.validated_data["until"],
            duration_days=duration_days,
        )
        payload["account"] = InsightsAccountSerializer(account).data
        return success_response(
            data=payload,
            message="Persisted account Insights snapshot fetched successfully.",
        )


class InsightsAccountSnapshotContentAPIView(APIView):
    """Read a database-paginated page from the published content version."""

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request, organization_id, social_account_id):
        query = InsightsSnapshotQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        organization, account = get_selected_account(
            user=request.user,
            organization_id=organization_id,
            social_account_id=social_account_id,
        )
        if query.validated_data["platform"] != account.platform:
            raise ValidationError({"platform": "platform must match the selected account."})

        since = query.validated_data["since"]
        until = query.validated_data["until"]
        duration_days = get_duration_slot_days(
            account=account,
            since=since,
            until=until,
        )
        queryset, sync = build_content_snapshot_read(
            account=account,
            duration_days=duration_days,
        )
        content_freshness = get_content_freshness(queryset=queryset, sync=sync)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        results = InsightsSnapshotMediaSerializer(page, many=True).data
        page_info = {
            "page": paginator.page.number,
            "page_size": paginator.get_page_size(request),
            "total_items": paginator.page.paginator.count,
            "total_pages": paginator.page.paginator.num_pages,
            "has_next": paginator.page.has_next(),
            "has_previous": paginator.page.has_previous(),
        }
        return success_response(
            data={
                "filters": {
                    "organization_id": organization.organization_id,
                    "social_account_id": str(account.id),
                    "platform": account.platform,
                    "since": since.isoformat(),
                    "until": until.isoformat(),
                },
                "content_performance": {
                    "availability": content_freshness["availability"],
                    "reason": content_freshness["reason"],
                    "status": content_freshness["status"],
                    "since": content_freshness["since"],
                    "until": content_freshness["until"],
                    "updated_at": content_freshness["updated_at"],
                    "results": results,
                    "pagination": page_info,
                },
                "freshness": {
                    "content": content_freshness,
                    "sync": sync,
                    "active_sync": sync["active_sync"],
                },
            },
            message="Persisted content Insights snapshots fetched successfully.",
        )


class InsightsAccountSyncAPIView(APIView):
    """Queue the existing background workflow for one account/date range."""

    permission_classes = [IsAuthenticated]

    def post(self, request, organization_id, social_account_id):
        serializer = InsightsSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data

        organization, account = get_selected_account(
            user=request.user,
            organization_id=organization_id,
            social_account_id=social_account_id,
        )
        if filters["platform"] != account.platform:
            raise ValidationError({"platform": "platform must match the selected account."})
        state, already_active = request_account_insights_sync(
            account=account,
            since=filters["since"],
            until=filters["until"],
            force_refresh=filters["force_refresh"],
        )
        data = {
            "organization_id": organization.organization_id,
            "social_account_id": str(account.id),
            "platform": account.platform,
            "since": state.since.isoformat(),
            "until": state.until.isoformat(),
            "sync_state_id": str(state.id),
            "status": state.status,
            "account_status": state.account_status,
            "progress": {
                "discovered": state.items_discovered,
                "processed": state.items_processed,
                "total": state.items_total,
            },
            "requested_at": state.requested_at.isoformat() if state.requested_at else None,
            "started_at": state.started_at.isoformat() if state.started_at else None,
            "completed_at": state.completed_at.isoformat() if state.completed_at else None,
            "already_active": already_active,
        }
        response_status = (
            status.HTTP_200_OK
            if state.status == InsightsSyncStatus.COMPLETE
            else status.HTTP_202_ACCEPTED
        )
        return success_response(
            data=data,
            message="Insights sync status returned successfully.",
            status_code=response_status,
        )
