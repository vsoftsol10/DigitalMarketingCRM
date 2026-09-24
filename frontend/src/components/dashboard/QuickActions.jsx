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
    <Card elevation={0} sx={{ border: "1px solid #E2E8F0", borderRadius: "22px", height: 520, display: "flex", flexDirection: "column" }}>
      <CardContent sx={{ p: 3, display: "flex", flexDirection: "column", flex: 1, "&:last-child": { pb: 3 } }}>
        <Typography sx={TYPOGRAPHY.sectionTitle}>Quick Actions</Typography>
        <Typography sx={{ ...TYPOGRAPHY.sectionDescription, mt: 0.5, mb: 3 }}>Jump to a common task</Typography>
        <Stack spacing={2}>
          {ACTIONS.map((action) => (
            <Box
              key={action.id}
              component="button"
              type="button"
              onClick={() => navigate(action.path)}
              sx={{ width: "100%", display: "flex", alignItems: "center", gap: 2, p: 2, border: "1px solid #E2E8F0", borderRadius: "16px", bgcolor: "transparent", textAlign: "left", cursor: "pointer", transition: "background-color 0.2s ease, border-color 0.2s ease", "&:hover": { bgcolor: "#F8FAFC", borderColor: "#CBD5E1" }, "&:focus-visible": { outline: "2px solid #2563EB", outlineOffset: "2px" } }}
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
