import {
  Box,
  Button,
  Stack,
  Typography,
} from "@mui/material";

import AddIcon from "@mui/icons-material/Add";
import SettingsSuggestOutlinedIcon from "@mui/icons-material/SettingsSuggestOutlined";

import { TYPOGRAPHY } from "../../theme/typography";

export default function PlansHeader({
  onCustomPlan,
  onCreatePlan,
}) {
  return (
    <Box
      sx={{
        width: "100%",
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: 3,

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
            fontWeight: 700,
            lineHeight: "36px",
            letterSpacing: "-0.02em",
            color: "#1E293B",
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
            color: "#64748B",
            mt: 0.5,
          }}
        >
          Manage subscription plans for organizations.
        </Typography>
      </Box>

      {/* RIGHT */}
      <Stack
        direction="row"
        spacing={1}
        sx={{
          flexShrink: 0,

          width: {
            xs: "100%",
            sm: "auto",
          },
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
            height: 46,
            px: 2,
            borderRadius: "12px",

            borderColor: "#D7DEE8",
            color: "#1E293B",
            backgroundColor: "#FFFFFF",

            fontSize: "14px",
            fontWeight: 600,
            lineHeight: "20px",
            textTransform: "none",

            whiteSpace: "nowrap",

            "&:hover": {
              backgroundColor: "#F8FAFC",
              borderColor: "#CBD5E1",
            },
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
            height: 46,
            px: 2.1,
            borderRadius: "12px",

            backgroundColor: "#2563EB",

            fontSize: "14px",
            fontWeight: 600,
            lineHeight: "20px",
            textTransform: "none",

            whiteSpace: "nowrap",

            "&:hover": {
              backgroundColor: "#1D4ED8",
            },
          }}
        >
          Create Plan
        </Button>
      </Stack>
    </Box>
  );
}