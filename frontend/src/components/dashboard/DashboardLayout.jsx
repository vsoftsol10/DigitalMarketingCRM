import { Grid } from "@mui/material";

export default function DashboardLayout({
  schedule,
  notifications,
  recentActivity,
  quickActions,
}) {
  return (
    <Grid
      container
      spacing={3}
      sx={{
        mt: 4,
      }}
    >
      {/* Schedule */}

      <Grid
        size={{
          xs: 12,
          lg: 8,
        }}
      >
        {schedule}
      </Grid>

      {/* Notifications */}

      <Grid
        size={{
          xs: 12,
          lg: 4,
        }}
      >
        {notifications}
      </Grid>

      {/* Recent Activity */}

      <Grid
        size={{
          xs: 12,
          lg: 8,
        }}
      >
        {recentActivity}
      </Grid>

      {/* Quick Actions */}

      <Grid
        size={{
          xs: 12,
          lg: 4,
        }}
      >
        {quickActions}
      </Grid>
    </Grid>
  );
}
