import { Box, Card, CardContent, Stack, Typography } from "@mui/material";
import ArrowForwardRoundedIcon from "@mui/icons-material/ArrowForwardRounded";
import { useNavigate } from "react-router-dom";

import { TYPOGRAPHY } from "../../theme/typography";
import QuickActionIcon from "./QuickActionIcon";

const ACTIONS = [
  { id: "create-post", title: "Create Post", path: "/posts", icon: "post" },
  { id: "content-planner", title: "Content Planner", path: "/planner", icon: "planner" },
  { id: "create-organization", title: "Create Organization", path: "/organizations/new", icon: "organization" },
  { id: "calendar", title: "Calendar", path: "/calendar", icon: "calendar" },
];

export default function QuickActions() {
  const navigate = useNavigate();

  return (
    <Card
      elevation={0}
      sx={{
        position: "relative",
        overflow: "hidden",
        border: "1px solid #DDE3F1",
        borderRadius: "20px",
        height: "auto",
        minHeight: { xs: 390, lg: 390 },
        display: "flex",
        flexDirection: "column",
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
          "&:last-child": { pb: 3 },
        }}
      >
        <Typography sx={TYPOGRAPHY.sectionTitle}>Quick Actions</Typography>
        <Typography sx={{ ...TYPOGRAPHY.sectionDescription, mt: 0.5, mb: 3 }}>Jump to a common task</Typography>
        <Stack spacing={1.25}>
          {ACTIONS.map((action) => (
            <Box
              key={action.id}
              component="button"
              type="button"
              onClick={() => navigate(action.path)}
              sx={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                gap: 1.5,
                minHeight: 60,
                p: 1.25,
                border: "1px solid #E2E8F0",
                borderRadius: "14px",
                background: "#FFFFFF",
                boxShadow: "none",
                textAlign: "left",
                cursor: "pointer",
                transition: "background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease",
                "&:hover": {
                  background: "#F8FAFC",
                  borderColor: "#C7D2FE",
                  boxShadow: "0 3px 8px rgba(31,41,80,.06)",
                },
                "&:focus-visible": { outline: "2px solid #2563EB", outlineOffset: "2px" },
              }}
            >
              <QuickActionIcon icon={action.icon} />
              <Typography sx={{ flex: 1, minWidth: 0, fontSize: 15, fontWeight: 600, color: "#1E293B", lineHeight: 1.4 }}>{action.title}</Typography>
              <ArrowForwardRoundedIcon sx={{ color: "#94A3B8", fontSize: 20, flexShrink: 0 }} />
            </Box>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
