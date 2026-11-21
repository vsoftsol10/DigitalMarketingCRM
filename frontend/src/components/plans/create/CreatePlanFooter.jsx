import { Box, Button } from "@mui/material";

import CheckIcon from "@mui/icons-material/Check";
import { planPrimaryButtonSx, planSecondaryButtonSx } from "../plansGlassSx";

export default function CreatePlanFooter({ onCancel, loading = false }) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: { xs: "column-reverse", sm: "row" },
        alignItems: "center",
        justifyContent: "flex-end",
        gap: 1.5,
        width: { xs: "100%", sm: "auto" },
      }}
    >
      {/* Cancel */}

      <Button
        type="button"
        variant="outlined"
        disabled={loading}
        onClick={onCancel}
        sx={{
          ...planSecondaryButtonSx,
          width: { xs: "100%", sm: 112 },
          minHeight: 48,
        }}
      >
        Cancel
      </Button>

      {/* Save */}

      <Button
        type="submit"
        variant="contained"
        disabled={loading}
        disableElevation
        startIcon={<CheckIcon sx={{ fontSize: 20 }} />}
        sx={{
          ...planPrimaryButtonSx,
          width: { xs: "100%", sm: "auto" },
          minWidth: { sm: 180 },
          minHeight: 48,
        }}
      >
        {loading ? "Creating Plan..." : "Save Plan"}
      </Button>
    </Box>
  );
}
