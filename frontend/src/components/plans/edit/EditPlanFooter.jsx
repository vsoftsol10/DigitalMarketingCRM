// EditPlanFooter.jsx
import { Box, Button } from "@mui/material";

import CheckIcon from "@mui/icons-material/Check";

export default function EditPlanFooter({
  onCancel,
  loading = false,
}) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "flex-end",
        gap: 1.5,
        width: "auto",
      }}
    >
      {/* CANCEL */}

      <Button
        type="button"
        variant="outlined"
        disabled={loading}
        onClick={onCancel}
        sx={{
          width: 100,
          height: 52,

          borderRadius: "14px",

          border: "1px solid #D7DEE8",

          backgroundColor: "#FFFFFF",

          color: "#334155",

          fontSize: "16px",
          fontWeight: 500,

          textTransform: "none",

          boxShadow: "none",

          "&:hover": {
            backgroundColor: "#FFFFFF",
            borderColor: "#CBD5E1",
            boxShadow: "none",
          },
        }}
      >
        Cancel
      </Button>

      {/* UPDATE PLAN */}

      <Button
        type="submit"
        variant="contained"
        disabled={loading}
        disableElevation
        startIcon={
          <CheckIcon
            sx={{
              fontSize: 20,
            }}
          />
        }
        sx={{
          width: 153,
          height: 52,

          borderRadius: "14px",

          backgroundColor: "#2563EB",

          color: "#FFFFFF",

          fontSize: "16px",
          fontWeight: 600,

          textTransform: "none",

          boxShadow: "none",

          "&:hover": {
            backgroundColor: "#1D4ED8",
            boxShadow: "none",
          },
        }}
      >
        {loading ? "Updating..." : "Update Plan"}
      </Button>
    </Box>
  );
}