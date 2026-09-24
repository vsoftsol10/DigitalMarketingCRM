import { Card, CardContent, Typography, Box } from "@mui/material";

import { TYPOGRAPHY } from "../../theme/typography";

import DashboardNotificationList from "./DashboardNotificationList";

export default function DashboardNotificationsCard({
  notifications = [],
  onNotificationClick,
}) {
  return (
    <Card
      elevation={0}
      sx={{
        border: "1px solid #E2E8F0",
        borderRadius: "22px",
        height: 520,

        display: "flex",
        flexDirection: "column",
        minHeight: 0,
      }}
    >
      <CardContent
        sx={{
          p: 3,

          display: "flex",
          flexDirection: "column",

          flex: 1,
          minHeight: 0,

          "&:last-child": {
            pb: 3,
          },
        }}
      >
        {/* Header */}

        <Typography sx={TYPOGRAPHY.sectionTitle}>Notifications</Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.sectionDescription,
            mt: 0.5,
            mb: 3,
          }}
        >
          {notifications.length} items need attention
        </Typography>

        {/* Empty State */}

        {notifications.length === 0 ? (
          <Box
            sx={{
              flex: 1,
              minHeight: 0,

              display: "flex",
              justifyContent: "center",
              alignItems: "center",

              color: "#94A3B8",

              fontSize: 15,
            }}
          >
            No notifications
          </Box>
        ) : (
          <Box
            sx={{
              flex: 1,
              minHeight: 0,

              overflowY: "auto",

              pr: 0.5,

              "&::-webkit-scrollbar": {
                width: 4,
              },

              "&::-webkit-scrollbar-thumb": {
                background: "#CBD5E1",
                borderRadius: 20,
              },
            }}
          >
            <DashboardNotificationList
              notifications={notifications}
              onNotificationClick={onNotificationClick}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
