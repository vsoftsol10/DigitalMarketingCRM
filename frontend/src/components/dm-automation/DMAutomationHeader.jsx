import { Add } from "@mui/icons-material";
import { Box, Button, Typography } from "@mui/material";

import { TYPOGRAPHY } from "../../theme/typography";

export default function DMAutomationHeader({ onCreateAutomation }) {
  return (
    <Box
      sx={{
        position: "relative",
        width: "100%",
        minHeight: 68,
      }}
    >
      {/* Page Title + Description */}
      <Box
        sx={{
          width: {
            xs: "100%",
            sm: "calc(100% - 220px)",
          },
        }}
      >
        <Typography sx={TYPOGRAPHY.pageTitle}>
          DM Automation
        </Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.pageDescription,
            mt: 0.25,
            whiteSpace: "nowrap",
          }}
        >
          Automatically respond to interactions on your Instagram content.
        </Typography>
      </Box>

      {/* Create Automation */}
      <Button
        variant="contained"
        startIcon={<Add />}
        onClick={onCreateAutomation}
        sx={{
          ...TYPOGRAPHY.button,

          position: {
            xs: "static",
            sm: "absolute",
          },

          top: {
            sm: 0,
          },

          right: {
            sm: 0,
          },

          width: {
            xs: "100%",
            sm: 195,
          },

          minWidth: {
            sm: 195,
          },

          height: 44,

          mt: {
            xs: 2,
            sm: 0,
          },

          px: 2,

          borderRadius: "12px",
          whiteSpace: "nowrap",

          boxShadow: "0 2px 4px rgba(37, 99, 235, 0.16)",

          "& .MuiButton-startIcon": {
            marginRight: 0.75,
          },

          "&:hover": {
            boxShadow: "0 3px 8px rgba(37, 99, 235, 0.20)",
          },
        }}
      >
        Create Automation
      </Button>
    </Box>
  );
}