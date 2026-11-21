import { Box, Typography } from "@mui/material";

import { TYPOGRAPHY } from "../../theme/typography";

export default function SettingsHeader() {
  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,
        maxWidth: 960,
        mx: "auto",
      }}
    >
      <Typography
        component="h1"
        sx={{
          ...TYPOGRAPHY.pageTitle,

          color: "#102347",

          fontSize: {
            xs: "28px",
            sm: "32px",
          },

          lineHeight: {
            xs: "36px",
            sm: "40px",
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

          color: "#667792",
        }}
      >
        Manage account and application settings.
      </Typography>
    </Box>
  );
}
