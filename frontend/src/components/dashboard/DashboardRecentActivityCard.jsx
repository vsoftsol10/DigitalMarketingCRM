import { Box, Card, CardContent, Typography } from "@mui/material";
import CheckCircleOutlineRoundedIcon from "@mui/icons-material/CheckCircleOutlineRounded";

import { TYPOGRAPHY } from "../../theme/typography";

import DashboardActivityList from "./DashboardActivityList";

export default function DashboardRecentActivityCard({
  activities = [],
  onActivityClick,
}) {
  return (
    <Card
      elevation={0}
      sx={{
        position: "relative",
        overflow: "hidden",
        border: "1px solid #DDE3F1",
        borderRadius: "20px",
        height: { xs: 390, lg: 390 },
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

        display: "flex",
        flexDirection: "column",
        minHeight: 0,
      }}
    >
      <CardContent
        sx={{
          position: "relative",
          zIndex: 1,
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

        <Typography sx={TYPOGRAPHY.sectionTitle}>
          Recent Activity
        </Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.sectionDescription,
            mt: 0.5,
            mb: 3,
          }}
        >
          Latest actions across your accounts
        </Typography>

        {/* Empty State */}

        {activities.length === 0 ? (
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
            <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 1.5 }}>
              <Box sx={{ width: 58, height: 58, borderRadius: "16px", display: "grid", placeItems: "center", bgcolor: "#F1F5F9", color: "#8292AE" }}>
                <CheckCircleOutlineRoundedIcon sx={{ fontSize: 26 }} />
              </Box>
              <Typography sx={{ fontSize: 16, fontWeight: 600, color: "#172554" }}>No recent activity</Typography>
              <Typography sx={{ fontSize: 14, color: "#64748B" }}>Latest actions across your accounts will appear here.</Typography>
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
            <DashboardActivityList
              activities={activities}
              onActivityClick={onActivityClick}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
