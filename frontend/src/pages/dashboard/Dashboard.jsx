import { useEffect, useState } from "react";

import DashboardHeader from "../../components/dashboard/DashboardHeader";
import DashboardStats from "../../components/dashboard/DashboardStats";

import dashboardService from "../../services/dashboard.service";
import DashboardScheduleCard from "../../components/dashboard/DashboardScheduleCard";
import { Box } from "@mui/material";
import DashboardLayout from "../../components/dashboard/DashboardLayout";
import DashboardNotificationsCard from "../../components/dashboard/DashboardNotificationsCard";
import DashboardRecentActivityCard from "../../components/dashboard/DashboardRecentActivityCard";
import DashboardQuickActionsCard from "../../components/dashboard/DashboardQuickActionsCard";
export default function Dashboard() {
  const [dashboard, setDashboard] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    const response = await dashboardService.getDashboard();

    setDashboard(response);
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
        onButtonClick={() => console.log("Create Post")}
      />

      <Box sx={{ mt: 4 }}>
        <DashboardStats statistics={dashboard.statistics} />
      </Box>

      <DashboardLayout
        schedule={
          <DashboardScheduleCard
            schedule={dashboard.today_schedule}
            onCreatePost={() => console.log("Create Post")}
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
        // quickActions={null}
        quickActions={
          <DashboardQuickActionsCard
            actions={dashboard.quick_actions}
            onActionClick={(action) => console.log(action)}
          />
        }
      />
    </>
  );
}
