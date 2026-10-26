import {
  Box,
  Button,
  Stack,
  Typography,
} from "@mui/material";

import AddIcon from "@mui/icons-material/Add";
import SettingsSuggestOutlinedIcon from "@mui/icons-material/SettingsSuggestOutlined";

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
            height: 46,
            px: 2,
            borderRadius: 999,
            borderColor: "rgba(255,255,255,0.95)",
            color: "#203965",
            background: "linear-gradient(145deg, rgba(255,255,255,0.9), rgba(233,243,255,0.82))",
            boxShadow: "0 7px 16px rgba(70,106,172,0.1), inset 0 1px 0 #FFFFFF",

            fontSize: "14px",
            fontWeight: 600,
            lineHeight: "20px",
            textTransform: "none",

            whiteSpace: "nowrap",
            flex: { xs: "1 1 auto", sm: "0 0 auto" },

            "&:hover": {
              background: "linear-gradient(145deg, #FFFFFF, #EAF3FF)",
              borderColor: "#B9CEF0",
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
            borderRadius: 999,
            background: "linear-gradient(105deg, #9358F2 0%, #5578F5 58%, #2C9BEB 100%)",
            boxShadow: "0 10px 20px rgba(106,91,224,0.24), inset 0 1px 0 rgba(255,255,255,0.45)",

            fontSize: "14px",
            fontWeight: 600,
            lineHeight: "20px",
            textTransform: "none",

            whiteSpace: "nowrap",
            flex: { xs: "1 1 auto", sm: "0 0 auto" },

            "&:hover": {
              background: "linear-gradient(105deg, #8549E9 0%, #496AEF 58%, #228CE1 100%)",
            },
          }}
        >
          Create Plan
        </Button>
      </Stack>
    </Box>
  );
}
