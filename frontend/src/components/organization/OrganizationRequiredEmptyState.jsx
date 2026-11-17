import { Box, Button, Stack, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { glassPrimaryButtonSx } from "../ui/form/glassFormSx";
import { TYPOGRAPHY } from "../../theme/typography";

const ORGANIZATION_CREATE_PATH = "/organizations/new";

export default function OrganizationRequiredEmptyState() {
  const navigate = useNavigate();

  return (
    <Box
      component="section"
      role="status"
      aria-label="Create Your First Organization"
      sx={{
        width: "100%",
        minHeight: "calc(100dvh - 144px)",
        display: "grid",
        placeItems: "center",
        px: { xs: 2, sm: 3 },
        py: 2,
        textAlign: "center",
      }}
    >
      <Stack spacing={1.5} alignItems="center" sx={{ width: "100%", maxWidth: 480 }}>
        <Typography
          component="h2"
          sx={{
            color: "#1E293B",
            fontWeight: 700,
            fontSize: { xs: 19, sm: 21 },
            lineHeight: 1.3,
          }}
        >
          Create Your First Organization
        </Typography>
        <Typography
          sx={{
            maxWidth: 440,
            color: "#64748B",
            fontSize: 14,
            lineHeight: 1.6,
          }}
        >
          You haven&apos;t created any organizations yet. Create an organization to start managing your social media content.
        </Typography>
        <Button
          variant="contained"
          size="small"
          onClick={() => navigate(ORGANIZATION_CREATE_PATH)}
          sx={{
            mt: 0.5,
            height: 48,
            px: 2.5,
            ...TYPOGRAPHY.button,
            ...glassPrimaryButtonSx,
          }}
        >
          Create Organization
        </Button>
      </Stack>
    </Box>
  );
}
