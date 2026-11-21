import { Box, Card, CardContent, Typography } from "@mui/material";

import { TYPOGRAPHY } from "../../theme/typography";

import DashboardQuickActionList from "./DashboardQuickActionList";

export default function DashboardQuickActionsCard({
  actions = [],
  onActionClick,
}) {
  return (
    <Card
      elevation={0}
      sx={{
        border: "1px solid #DDE3F1",
        borderRadius: "20px",
        height: { xs: 420, lg: 390 },
        background: "#FFFFFF",
        boxShadow: "0 4px 12px rgba(41,55,103,.045)",

        display: "flex",
        flexDirection: "column",
      }}
    >
      <CardContent
        sx={{
          p: 3,

          display: "flex",
          flexDirection: "column",

          flex: 1,

          "&:last-child": {
            pb: 3,
          },
        }}
      >
        <Typography sx={TYPOGRAPHY.sectionTitle}>Quick Actions</Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.sectionDescription,
            mt: 0.5,
            mb: 3,
          }}
        >
          Jump to a common task
        </Typography>

        {actions.length === 0 ? (
          <Box
            sx={{
              flex: 1,

              display: "flex",
              justifyContent: "center",
              alignItems: "center",

              color: "#94A3B8",

              fontSize: 15,
            }}
          >
            No actions available
          </Box>
        ) : (
          <DashboardQuickActionList
            actions={actions}
            onActionClick={onActionClick}
          />
        )}
      </CardContent>
    </Card>
  );
}
