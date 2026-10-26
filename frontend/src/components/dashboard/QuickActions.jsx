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
        border: "1px solid rgba(255,255,255,.9)",
        borderRadius: "24px",
        height: { xs: 390, lg: 370 },
        display: "flex",
        flexDirection: "column",
        background: "linear-gradient(145deg, rgba(250,252,255,.98), rgba(241,246,255,.95))",
        boxShadow: "0 14px 28px rgba(75,96,151,.12), 0 3px 8px rgba(79,99,154,.07), inset 0 2px 0 rgba(255,255,255,.98), inset 0 -2px 5px rgba(112,127,177,.06)",
        "&::before": {
          content: "\"\"",
          position: "absolute",
          inset: 4,
          borderRadius: "20px",
          border: "1px solid rgba(255,255,255,.8)",
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
        <Stack spacing={2}>
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
                gap: 2,
                p: 1.7,
                border: "1px solid rgba(255,255,255,.92)",
                borderRadius: "16px",
                background: "linear-gradient(115deg, rgba(235,242,255,.84), rgba(255,255,255,.72))",
                boxShadow: "0 5px 12px rgba(76,98,154,.09), inset 0 1px 0 rgba(255,255,255,.98), inset 0 -1px 2px rgba(94,111,159,.06)",
                textAlign: "left",
                cursor: "pointer",
                transition: "background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease",
                "&:hover": {
                  background: "linear-gradient(115deg, rgba(229,238,255,.96), rgba(250,252,255,.9))",
                  borderColor: "rgba(126,148,202,.3)",
                  boxShadow: "0 7px 15px rgba(76,98,154,.13), inset 0 1px 0 rgba(255,255,255,.98)",
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
