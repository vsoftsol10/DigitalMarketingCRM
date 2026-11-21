import { Card, CardContent, Typography, Box } from "@mui/material";
import NotificationsActiveOutlinedIcon from "@mui/icons-material/NotificationsActiveOutlined";

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
        position: "relative",
        overflow: "hidden",
        border: "1px solid #DDE3F1",
        borderRadius: "20px",
        height: { xs: 400, lg: 450 },
        background: "#FFFFFF",
        boxShadow: "0 4px 12px rgba(41,55,103,.045)",
        "&::before": {
          content: "\"\"",
          position: "absolute",
          inset: 4,
          borderRadius: "20px",
          border: "none",
          pointerEvents: "none",
        },
        "&::after": {
          content: "\"\"",
          position: "absolute",
          display: "none",
          pointerEvents: "none",
        },

        display: "flex",
        flexDirection: "column",
        minHeight: 0,
      }}
    >
      <CardContent
        sx={{
          position: "relative",
          zIndex: 1,
          p: { xs: 2.5, md: 3 },

          display: "flex",
          flexDirection: "column",

          flex: 1,
          minHeight: 0,

          "&:last-child": {
            pb: { xs: 2.5, md: 3 },
          },
        }}
      >
        {/* Header */}

        <Typography sx={TYPOGRAPHY.sectionTitle}>Need Attention</Typography>

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

              color: "#64748B",

              fontSize: 15,
              textAlign: "center",
            }}
          >
            <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 1.5 }}>
              <Box sx={{ position: "relative", width: 58, height: 58, borderRadius: "16px", display: "grid", placeItems: "center", bgcolor: "#FFF1F2", border: "1px solid #FFE4E6", boxShadow: "none" }}>
                <NotificationsActiveOutlinedIcon sx={{ fontSize: 26, color: "#E11D48" }} />
              </Box>
              <Typography sx={{ fontSize: 16, fontWeight: 600, color: "#172554" }}>
                Nothing needs attention
              </Typography>
              <Typography sx={{ fontSize: 14, color: "#64748B" }}>
                No urgent items at the moment.
              </Typography>
            </Box>
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
