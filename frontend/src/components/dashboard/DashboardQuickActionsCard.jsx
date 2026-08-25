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
        border: "1px solid #E2E8F0",
        borderRadius: "22px",
        height: 520,

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
