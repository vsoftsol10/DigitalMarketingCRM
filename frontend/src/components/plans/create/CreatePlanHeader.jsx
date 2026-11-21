import {
  Box,
  Button,
  Stack,
  Typography,
} from "@mui/material";

import ArrowBackIcon from "@mui/icons-material/ArrowBack";

import { TYPOGRAPHY } from "../../../theme/typography";
import { planSecondaryButtonSx } from "../plansGlassSx";

export default function CreatePlanHeader({ onBack }) {
  return (
    <Box
      sx={{
        width: "100%",

        /*
         * Original UI header spacing
         */
        pt: {
          xs: 3,
          sm: 3.5,
          md: 4,
        },

        pb: {
          xs: 3,
          md: 3.5,
        },

        boxSizing: "border-box",
      }}
    >
      <Stack
        direction={{ xs: "column", sm: "row" }}
        alignItems={{ xs: "stretch", sm: "flex-start" }}
        justifyContent="space-between"
        spacing={{ xs: 1.5, sm: 0 }}
        sx={{
          width: "100%",
          minWidth: 0,
        }}
      >
        {/* =========================
            LEFT
        ========================= */}

        <Box
          sx={{
            minWidth: 0,
            flex: 1,
          }}
        >
          <Typography
            component="h1"
            sx={{
              ...TYPOGRAPHY.pageTitle,

              /*
               * Create Plan original UI size
               */
              fontSize: {
                xs: "25px",
                sm: "28px",
                md: "30px",
              },

              lineHeight: {
                xs: "32px",
                sm: "36px",
                md: "38px",
              },

              fontWeight: 700,

              color: "#12264D",

              m: 0,
            }}
          >
            Create Plan
          </Typography>

          <Typography
            component="p"
            sx={{
              ...TYPOGRAPHY.pageDescription,

              fontSize: {
                xs: "14px",
                sm: "15px",
              },

              lineHeight: "24px",

              color: "#647A9B",

              mt: 0.5,

              mb: 0,
            }}
          >
            Create and configure a subscription plan for your organizations.
          </Typography>
        </Box>

        {/* =========================
            RIGHT - BACK BUTTON
        ========================= */}

        <Button
          type="button"
          variant="outlined"
          startIcon={
            <ArrowBackIcon
              sx={{
                fontSize: 20,
              }}
            />
          }
          onClick={onBack}
          sx={{
            ...planSecondaryButtonSx,
            flexShrink: 0,
            minHeight: 46,
            minWidth: { xs: "100%", sm: 112 },
            ml: { xs: 0, sm: 3 },
            mt: 0.25,
          }}
        >
          Back
        </Button>
      </Stack>
    </Box>
  );
}
