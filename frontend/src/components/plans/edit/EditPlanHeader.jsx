// EditPlanHeader.jsx
import { Box, Button, Stack, Typography } from "@mui/material";

import ArrowBackIcon from "@mui/icons-material/ArrowBack";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function EditPlanHeader({ onBack }) {
  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,

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
        direction="row"
        alignItems="flex-start"
        justifyContent="space-between"
        sx={{
          width: "100%",
          minWidth: 0,
        }}
      >
        {/* LEFT */}

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

              fontSize: {
                xs: "28px",
                sm: "30px",
                md: "32px",
              },

              lineHeight: {
                xs: "36px",
                sm: "38px",
                md: "40px",
              },

              fontWeight: 700,

              color: "#12264D",

              m: 0,
            }}
          >
            Edit Plan
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
            Update plan details
          </Typography>
        </Box>

        {/* RIGHT - BACK BUTTON */}

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
            flexShrink: 0,

            height: 52,

            minWidth: 112,

            px: 2.25,

            ml: 3,

            mt: 0.25,

            borderRadius: 999,

            borderColor: "rgba(255,255,255,0.95)",

            color: "#203965",

            background: "linear-gradient(145deg, rgba(255,255,255,0.9), rgba(233,243,255,0.82))",

            fontSize: "15px",

            fontWeight: 500,

            lineHeight: "20px",

            textTransform: "none",

            boxShadow: "0 7px 16px rgba(70,106,172,0.1), inset 0 1px 0 #FFFFFF",

            "&:hover": {
              borderColor: "#B9CEF0",

              background: "linear-gradient(145deg, #FFFFFF, #EAF3FF)",

              boxShadow: "0 8px 18px rgba(70,106,172,0.14), inset 0 1px 0 #FFFFFF",
            },
          }}
        >
          Back
        </Button>
      </Stack>
    </Box>
  );
}
