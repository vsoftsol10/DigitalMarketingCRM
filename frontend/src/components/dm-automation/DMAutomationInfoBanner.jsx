import { Instagram } from "@mui/icons-material";
import { Box, Stack, Typography } from "@mui/material";

import { TYPOGRAPHY } from "../../theme/typography";

export default function DMAutomationInfoBanner({ activeCount }) {
  return (
    <Box
      sx={{
        mt: 3,
        width: "100%",
        px: { xs: 2, sm: 2.5 },
        py: 2,
        borderRadius: "18px",
        border: "1px solid #F3DCE8",
        backgroundColor: "#FFFFFF",
        boxShadow: "0 1px 3px rgba(15, 23, 42, 0.04)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        spacing={1.5}
        sx={{
          width: "100%",
        }}
      >
        <Box
          sx={{
            width: 40,
            height: 40,
            borderRadius: "12px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "#FFF1F7",
            flexShrink: 0,
          }}
        >
          <Instagram
            sx={{
              fontSize: 22,
              color: "#EC4899",
            }}
          />
        </Box>

        <Typography
          sx={{
            ...TYPOGRAPHY.body,
            color: "#64748B",
            display: "flex",
            alignItems: "center",
            flexWrap: "wrap",
            lineHeight: "40px", // icon height (40) oda match agum
          }}
        >
          DM Automation works with your{" "}
          <Box
            component="span"
            sx={{
              fontWeight: 600,
              color: "#1E293B",
              mx: 0.5,
            }}
          >
            Instagram
          </Box>
          content — Posts, Reels, and Carousels.
          <Box
            component="span"
            sx={{
              color: "#64748B",
              mx: 0.5,
            }}
          >
            · {activeCount} active automations
          </Box>
        </Typography>
      </Stack>
    </Box>
  );
}