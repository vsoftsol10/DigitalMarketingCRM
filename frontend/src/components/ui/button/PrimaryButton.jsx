import { Button } from "@mui/material";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function PrimaryButton({
  children,
  fullWidth = true,
  height = 52,
  startIcon,
  endIcon,
  loading = false,
  disabled = false,
  type = "button",
  onClick,
}) {
  return (
    <Button
      type={type}
      variant="contained"
      fullWidth={fullWidth}
      disableElevation
      startIcon={startIcon}
      endIcon={endIcon}
      disabled={disabled || loading}
      onClick={onClick}
      sx={{
        height,

        borderRadius: "16px",

        bgcolor: "#2563EB",

        color: "#FFFFFF",

        ...TYPOGRAPHY.formButton,

        "&:hover": {
          bgcolor: "#1D4ED8",
        },
      }}
    >
      {children}
    </Button>
  );
}