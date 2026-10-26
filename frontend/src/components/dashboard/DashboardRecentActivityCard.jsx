import { Box, Card, CardContent, Typography } from "@mui/material";

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
        border: "1px solid rgba(255,255,255,.9)",
        borderRadius: "24px",
        height: { xs: 390, lg: 370 },
        background: "linear-gradient(145deg, rgba(250,252,255,.98) 0%, rgba(242,247,255,.95) 100%)",
        boxShadow: "0 14px 28px rgba(75,96,151,.12), 0 3px 8px rgba(79,99,154,.07), inset 0 2px 0 rgba(255,255,255,.98), inset 0 -2px 5px rgba(112,127,177,.06)",
        "&::before": {
          content: "\"\"",
          position: "absolute",
          inset: 4,
          borderRadius: "20px",
          border: "1px solid rgba(255,255,255,.8)",
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
            No recent activity
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
