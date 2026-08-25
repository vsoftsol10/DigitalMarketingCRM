import { Button } from "@mui/material";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function SecondaryButton({
  children,
  fullWidth = true,
  height = 52,
  startIcon,
  endIcon,
  disabled = false,
  type = "button",
  onClick,
}) {
  return (
    <Button
      type={type}
      variant="outlined"
      fullWidth={fullWidth}
      startIcon={startIcon}
      endIcon={endIcon}
      disabled={disabled}
      onClick={onClick}
      sx={{
        height,

        borderRadius: "16px",

        borderColor: "#E2E8F0",

        color: "#334155",

        bgcolor: "#FFFFFF",

        ...TYPOGRAPHY.formButton,

        "&:hover": {
          borderColor: "#CBD5E1",

          bgcolor: "#F8FAFC",
        },
      }}
    >
      {children}
    </Button>
  );
}