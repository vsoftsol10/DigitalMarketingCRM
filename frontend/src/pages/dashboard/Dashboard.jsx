import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import DashboardHeader from "../../components/dashboard/DashboardHeader";
import DashboardStats from "../../components/dashboard/DashboardStats";

import dashboardService from "../../services/dashboard.service";
import DashboardScheduleCard from "../../components/dashboard/DashboardScheduleCard";
import { Box } from "@mui/material";
import DashboardLayout from "../../components/dashboard/DashboardLayout";
import DashboardNotificationsCard from "../../components/dashboard/DashboardNotificationsCard";
import DashboardRecentActivityCard from "../../components/dashboard/DashboardRecentActivityCard";
import QuickActions from "../../components/dashboard/QuickActions";
import LoadingState from "../../components/ui/LoadingState";
import ErrorState from "../../components/ui/ErrorState";
import { formatApiErrorMessage } from "../../utils/apiErrorMessage";
export default function Dashboard() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const isMounted = useRef(false);

  const loadDashboard = useCallback(async () => {
    if (!isMounted.current) return;
    setIsLoading(true);
    setError("");

    try {
      const response = await dashboardService.getDashboard();

      if (!response || typeof response !== "object") {
        throw new Error("Dashboard data was not returned.");
      }

      if (isMounted.current) setDashboard(response);
    } catch (error) {
      console.error("Failed to load dashboard:", error);
      if (isMounted.current) {
        setError(formatApiErrorMessage(error, {
          fallback: "Unable to load the dashboard. Please try again.",
        }));
      }
    } finally {
      if (isMounted.current) setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    isMounted.current = true;
    Promise.resolve().then(() => {
      if (active) loadDashboard();
    });

    return () => {
      active = false;
      isMounted.current = false;
    };
  }, [loadDashboard]);

  if (isLoading && !dashboard) {
    return <LoadingState page="Dashboard" />;
  }

  if (error && !dashboard) {
    return <ErrorState message={error} onRetry={loadDashboard} variant="page" />;
  }

  if (!dashboard) {
    return <ErrorState message="Dashboard data is unavailable." onRetry={loadDashboard} variant="page" />;
  }

  return (
    <>
      {isLoading && <LoadingState label="UPDATING DASHBOARD..." variant="inline" />}
      {error && <ErrorState message={error} onRetry={loadDashboard} variant="inline" />}
      <DashboardHeader
        title="Dashboard"
        description="Monitor your marketing activities and today's tasks."
        buttonLabel="Create Post"
        onButtonClick={() => navigate("/posts")}
      />

      <Box sx={{ mt: 3 }}>
        <DashboardStats statistics={dashboard.statistics} />
      </Box>

      <DashboardLayout
        schedule={
          <DashboardScheduleCard
            schedule={dashboard.today_schedule}
            onCreatePost={() => navigate("/posts")}
          />
        }
        notifications={
          <DashboardNotificationsCard
            notifications={dashboard.notifications}
            onNotificationClick={(notification) => console.log(notification)}
          />
        }
        recentActivity={
          <DashboardRecentActivityCard
            activities={dashboard.recent_activities}
            onActivityClick={(activity) => console.log(activity)}
          />
        }
        quickActions={<QuickActions />}
      />
    </>
  );
}
