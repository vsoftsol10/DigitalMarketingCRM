import { Box, Typography } from "@mui/material";

import { TYPOGRAPHY } from "../../theme/typography";

export default function SettingsHeader() {
  return (
    <Box
      sx={{
        width: "100%",
        maxWidth: 840,
        mx: "auto",
      }}
    >
      <Typography
        component="h1"
        sx={{
          ...TYPOGRAPHY.pageTitle,

          color: "text.primary",

          fontSize: {
            xs: "28px",
            sm: "30px",
          },

          lineHeight: {
            xs: "36px",
            sm: "38px",
          },

          fontWeight: 700,
        }}
      >
        Settings
      </Typography>

      <Typography
        component="p"
        sx={{
          ...TYPOGRAPHY.body,

          mt: 0.5,

          color: "text.secondary",
        }}
      >
        Manage account and application settings.
      </Typography>
    </Box>
  );
}