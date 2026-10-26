import { Card, CardContent, Typography, Box } from "@mui/material";
import NotificationsActiveOutlinedIcon from "@mui/icons-material/NotificationsActiveOutlined";
import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";

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
        border: "1px solid rgba(255,255,255,.9)",
        borderRadius: "24px",
        height: { xs: 360, lg: 390 },
        background: "linear-gradient(145deg, rgba(255,241,245,.98) 0%, rgba(255,225,233,.96) 100%)",
        boxShadow: "0 16px 30px rgba(166, 90, 119, .14), 0 3px 8px rgba(180,92,124,.08), inset 0 2px 0 rgba(255,255,255,.98), inset 0 -2px 5px rgba(192,104,132,.08)",
        "&::before": {
          content: "\"\"",
          position: "absolute",
          inset: 4,
          borderRadius: "20px",
          border: "1px solid rgba(255,255,255,.72)",
          pointerEvents: "none",
        },
        "&::after": {
          content: "\"\"",
          position: "absolute",
          width: 150,
          height: 150,
          top: -70,
          right: -50,
          borderRadius: "50%",
          bgcolor: "rgba(226,98,134,.07)",
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

              color: "#D84E73",

              fontSize: 15,
              textAlign: "center",
            }}
          >
            <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 1.5 }}>
              <Box sx={{ position: "relative", width: 82, height: 82, borderRadius: "50%", display: "grid", placeItems: "center", background: "linear-gradient(145deg, rgba(255,236,243,.98), rgba(255,218,230,.94))", border: "3px solid rgba(255,255,255,.94)", boxShadow: "0 10px 21px rgba(219,87,126,.2), 0 2px 5px rgba(180,76,115,.12), inset 0 2px 3px rgba(255,255,255,.96), inset 0 -3px 5px rgba(216,90,129,.14)" }}>
                <NotificationsActiveOutlinedIcon sx={{ fontSize: 34, color: "#E5557A" }} />
                <AutoAwesomeRoundedIcon aria-hidden="true" sx={{ position: "absolute", top: 5, right: -24, fontSize: 16, color: "#E67C9A" }} />
                <AutoAwesomeRoundedIcon aria-hidden="true" sx={{ position: "absolute", bottom: 8, left: -22, fontSize: 13, color: "#E67C9A", opacity: .75 }} />
              </Box>
              <Typography sx={{ fontSize: 17, fontWeight: 700, color: "#263451" }}>
                Nothing needs attention
              </Typography>
              <Typography sx={{ fontSize: 14, color: "#74819F" }}>
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
