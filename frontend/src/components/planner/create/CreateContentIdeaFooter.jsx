import { Box, Button } from "@mui/material";
import { TYPOGRAPHY } from "../../../theme/typography";

export default function CreateContentIdeaFooter({ loading = false, onCancel }) {
  return (
    <Box
      sx={{
        mt: 5,
        pt: 3,

        borderTop: "1px solid #E2E8F0",

        display: "flex",
        justifyContent: "flex-end",
        gap: 2,
      }}
    >
      {/* Cancel */}

      <Button
        variant="outlined"
        onClick={onCancel}
        sx={{
          minWidth: 140,
          height: 48,

          borderRadius: "14px",

          borderColor: "#CBD5E1",

          color: "#475569",

          ...TYPOGRAPHY.formButton,

          "&:hover": {
            borderColor: "#94A3B8",
            bgcolor: "#F8FAFC",
          },
        }}
      >
        Cancel
      </Button>

      {/* Submit */}

      <Button
        type="submit"
        variant="contained"
        disabled={loading}
        sx={{
          minWidth: 180,
          height: 48,

          borderRadius: "14px",

          boxShadow: "none",

          ...TYPOGRAPHY.formButton,

          "&:hover": {
            boxShadow: "none",
          },
        }}
      >
        {loading ? "Creating..." : "Create Idea"}
      </Button>
    </Box>
  );
}
