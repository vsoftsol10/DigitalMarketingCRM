import { Box, Button } from "@mui/material";

import CheckIcon from "@mui/icons-material/Check";

export default function CreatePlanFooter({ onCancel, loading = false }) {
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
      {/* Cancel */}

      <Button
        type="button"
        variant="outlined"
        disabled={loading}
        onClick={onCancel}
        sx={{
          width: 100,
          height: 52,

          borderRadius: 999,

          border: "1px solid rgba(255,255,255,0.96)",

          background: "linear-gradient(145deg, rgba(255,255,255,0.92), rgba(234,243,255,0.82))",

          color: "#30466A",

          fontSize: "16px",
          fontWeight: 500,

          textTransform: "none",

          boxShadow: "0 6px 14px rgba(70,106,172,0.1), inset 0 1px 0 #FFFFFF",

          "&:hover": {
            background: "linear-gradient(145deg, #FFFFFF, #EAF3FF)",
            borderColor: "#B9CEF0",
            boxShadow: "0 8px 18px rgba(70,106,172,0.14), inset 0 1px 0 #FFFFFF",
          },
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
          minWidth: 180,
          height: 52,

          borderRadius: 999,

          background: "linear-gradient(105deg, #9358F2 0%, #5578F5 58%, #2C9BEB 100%)",

          color: "#FFFFFF",

          fontSize: "16px",
          fontWeight: 600,

          textTransform: "none",

          boxShadow: "0 10px 20px rgba(106,91,224,0.24), inset 0 1px 0 rgba(255,255,255,0.45)",

          "&:hover": {
            background: "linear-gradient(105deg, #8549E9 0%, #496AEF 58%, #228CE1 100%)",
            boxShadow: "0 12px 22px rgba(106,91,224,0.3), inset 0 1px 0 rgba(255,255,255,0.45)",
          },
        }}
      >
        {loading ? "Creating Plan..." : "Save Plan"}
      </Button>
    </Box>
  );
}
