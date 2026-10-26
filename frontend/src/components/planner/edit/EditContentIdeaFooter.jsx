import { Box, Button } from "@mui/material";

import { TYPOGRAPHY } from "../../../theme/typography";
import PrimaryButton from "../../ui/button/PrimaryButton";
import { glassPrimaryButtonSx } from "../../ui/form/glassFormSx";

export default function EditContentIdeaFooter({ loading = false, onCancel }) {
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

      {/* Update */}

      <PrimaryButton
        type="submit"
        loading={loading}
        fullWidth={false}
        height={48}
        sx={{
          minWidth: 180,
          ...TYPOGRAPHY.formButton,
          ...glassPrimaryButtonSx,
        }}
      >
        {loading ? "Updating..." : "Update Idea"}
      </PrimaryButton>
    </Box>
  );
}
