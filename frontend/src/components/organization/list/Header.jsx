import { Box, Typography, Button } from "@mui/material";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import { useNavigate } from "react-router-dom";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function Header({
  title,
  description,
  buttonLabel,
  buttonPath,
}) {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        mb: 5,
      }}
    >
      <Box>
        <Typography sx={TYPOGRAPHY.pageTitle}>{title}</Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.pageDescription,
            mt: 1,
          }}
        >
          {description}
        </Typography>
      </Box>

      <Button
        variant="contained"
        startIcon={<AddRoundedIcon />}
        onClick={() => navigate(buttonPath)}
        sx={{
          height: 48,
          px: 3,
          borderRadius: "14px",
          textTransform: "none",

          ...TYPOGRAPHY.button,

          bgcolor: "#2563EB",
          boxShadow: "none",

          "&:hover": {
            bgcolor: "#1D4ED8",
            boxShadow: "none",
          },
        }}
      >
        {buttonLabel}
      </Button>
    </Box>
  );
}
