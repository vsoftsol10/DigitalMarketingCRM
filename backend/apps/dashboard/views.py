from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import success_response

from .selectors import get_dashboard_data
from .serializers import DashboardSerializer


class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        dashboard = get_dashboard_data(user=request.user)
        return success_response(
            data=DashboardSerializer(dashboard).data,
            message="Dashboard fetched successfully.",
        )
