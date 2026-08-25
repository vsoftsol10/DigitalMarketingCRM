import { Button } from "@mui/material";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function TextButton({
  children,
  startIcon,
  endIcon,
  disabled = false,
  type = "button",
  onClick,
}) {
  return (
    <Button
      type={type}
      variant="text"
      startIcon={startIcon}
      endIcon={endIcon}
      disabled={disabled}
      onClick={onClick}
      sx={{
        color: "#475569",

        ...TYPOGRAPHY.formButton,

        "&:hover": {
          bgcolor: "#F8FAFC",
        },
      }}
    >
      {children}
    </Button>
  );
}