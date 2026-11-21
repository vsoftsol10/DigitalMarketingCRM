import { Box, Button } from "@mui/material";

import { TYPOGRAPHY } from "../../../theme/typography";
import PrimaryButton from "../../ui/button/PrimaryButton";
import { plannerPrimaryButtonSx, plannerSecondaryButtonSx } from "../plannerUiSx";

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
        flexDirection: { xs: "column-reverse", sm: "row" },
      }}
    >
      {/* Cancel */}

      <Button
        variant="outlined"
        onClick={onCancel}
        sx={{
          ...plannerSecondaryButtonSx,
          minWidth: { xs: "100%", sm: 140 },
          height: 48,

          ...TYPOGRAPHY.formButton,

          "&:hover": {
            borderColor: "#B9C4D8",
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
          ...TYPOGRAPHY.formButton,
          ...plannerPrimaryButtonSx,
          minWidth: { xs: "100%", sm: 180 },
        }}
      >
        {loading ? "Updating..." : "Update Idea"}
      </PrimaryButton>
    </Box>
  );
}
