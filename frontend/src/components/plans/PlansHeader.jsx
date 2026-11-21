import {
  Box,
  Button,
  Stack,
  Typography,
} from "@mui/material";

import AddIcon from "@mui/icons-material/Add";
import SettingsSuggestOutlinedIcon from "@mui/icons-material/SettingsSuggestOutlined";
import { planPrimaryButtonSx, planSecondaryButtonSx } from "./plansGlassSx";

export default function PlansHeader({
  onCustomPlan,
  onCreatePlan,
}) {
  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,
        display: "flex",
        alignItems: { xs: "stretch", sm: "flex-start" },
        justifyContent: "space-between",
        gap: { xs: 2, md: 3 },

        flexDirection: {
          xs: "column",
          sm: "row",
        },
      }}
    >
      {/* LEFT */}
      <Box sx={{ minWidth: 0 }}>
        <Typography
          component="h1"
          sx={{
            fontSize: "28px",
            fontWeight: 750,
            lineHeight: "36px",
            color: "#12264D",
            letterSpacing: "-0.03em",
          }}
        >
          Plans
        </Typography>

        <Typography
          component="p"
          sx={{
            fontSize: "15px",
            fontWeight: 400,
            lineHeight: "22px",
            color: "#647A9B",
            mt: 0.5,
          }}
        >
          Manage subscription plans for organizations.
        </Typography>
      </Box>

      {/* RIGHT */}
      <Stack
        direction="row"
        spacing={{ xs: 0.75, md: 1 }}
        sx={{
          flexShrink: 0,
          flexWrap: { xs: "wrap", sm: "nowrap" },
          width: { xs: "100%", sm: "auto" },
        }}
      >
        <Button
          variant="outlined"
          startIcon={
            <SettingsSuggestOutlinedIcon
              sx={{
                fontSize: 18,
              }}
            />
          }
          onClick={onCustomPlan}
          sx={{
            ...planSecondaryButtonSx,
            minHeight: 48,

            fontSize: "14px",
            fontWeight: 600,
            lineHeight: "20px",
            textTransform: "none",

            whiteSpace: "nowrap",
            flex: { xs: "1 1 auto", sm: "0 0 auto" },

          }}
        >
          Custom Plan
        </Button>

        <Button
          variant="contained"
          disableElevation
          startIcon={
            <AddIcon
              sx={{
                fontSize: 20,
              }}
            />
          }
          onClick={onCreatePlan}
          sx={{
            ...planPrimaryButtonSx,
            minHeight: 48,

            fontSize: "14px",
            fontWeight: 600,
            lineHeight: "20px",
            textTransform: "none",

            whiteSpace: "nowrap",
            flex: { xs: "1 1 auto", sm: "0 0 auto" },

          }}
        >
          Create Plan
        </Button>
      </Stack>
    </Box>
  );
}
