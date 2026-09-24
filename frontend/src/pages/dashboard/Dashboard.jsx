import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import DashboardHeader from "../../components/dashboard/DashboardHeader";
import DashboardStats from "../../components/dashboard/DashboardStats";

import dashboardService from "../../services/dashboard.service";
import DashboardScheduleCard from "../../components/dashboard/DashboardScheduleCard";
import { Box, CircularProgress, Typography } from "@mui/material";
import DashboardLayout from "../../components/dashboard/DashboardLayout";
import DashboardNotificationsCard from "../../components/dashboard/DashboardNotificationsCard";
import DashboardRecentActivityCard from "../../components/dashboard/DashboardRecentActivityCard";
import QuickActions from "../../components/dashboard/QuickActions";
export default function Dashboard() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function loadDashboard() {
      try {
        const response = await dashboardService.getDashboard();

        if (isMounted) {
          setDashboard(response);
        }
      } catch {
        if (isMounted) {
          setError("Unable to load the dashboard. Please try again.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      isMounted = false;
    };
  }, []);

  if (isLoading) {
    return (
      <Box
        sx={{
          minHeight: 320,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <CircularProgress size={32} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box
        role="alert"
        sx={{
          minHeight: 320,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#DC2626",
        }}
      >
        <Typography>{error}</Typography>
      </Box>
    );
  }

  if (!dashboard) {
    return null;
  }

  return (
    <>
      <DashboardHeader
        title="Dashboard"
        description="Monitor your marketing activities and today's tasks."
        buttonLabel="Create Post"
        onButtonClick={() => navigate("/posts")}
      />

      <Box sx={{ mt: 4 }}>
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
