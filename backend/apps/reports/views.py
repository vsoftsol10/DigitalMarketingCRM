from datetime import date

from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.responses import success_response
from apps.insights.services import get_selected_account
from apps.insights.snapshot_read import get_duration_slot_days

from .rendering import ReportRenderError, render_report_png
from .serializers import InsightsReportPreviewSerializer, InsightsReportRenderSerializer
from .services import build_insights_report_payload, validate_report_render_token


class InsightsReportPreviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InsightsReportPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        organization, account = get_selected_account(
            user=request.user,
            organization_id=values["organization_id"],
            social_account_id=values["social_account_id"],
        )
        if account.platform != values["platform"]:
            return Response({
                "success": False,
                "message": "The selected platform does not match this account.",
                "errors": {"platform": "The selected platform does not match this account."},
            }, status=status.HTTP_400_BAD_REQUEST)

        report_payload = build_insights_report_payload(
            user=request.user,
            organization=organization,
            account=account,
            since=values["since"],
            until=values["until"],
            mode=values["mode"],
            meta_ads=values["meta_ads"],
        )
        return success_response(
            data=report_payload,
            message="Saved Insights report preview prepared successfully.",
        )


class InsightsReportPngAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InsightsReportRenderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        render_claim = validate_report_render_token(
            token=serializer.validated_data["render_token"],
            user=request.user,
        )
        _organization, account = get_selected_account(
            user=request.user,
            organization_id=render_claim["organization_id"],
            social_account_id=render_claim["social_account_id"],
        )
        since = date.fromisoformat(render_claim["since"])
        until = date.fromisoformat(render_claim["until"])
        duration_days = get_duration_slot_days(account=account, since=since, until=until)
        if duration_days != render_claim["duration_days"]:
            return Response({
                "success": False,
                "message": "The saved report range is no longer valid.",
                "errors": {"date_range": "The saved report range is no longer valid."},
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            png = render_report_png(html=serializer.validated_data["html"])
        except ReportRenderError:
            return Response({
                "success": False,
                "message": "The report image could not be generated. Please try again.",
                "errors": {"render": "The report image renderer is unavailable."},
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        response = HttpResponse(png, content_type="image/png")
        response["Content-Disposition"] = 'inline; filename="insights-report.png"'
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
