import { Box, Button, Typography } from "@mui/material";

import AddRoundedIcon from "@mui/icons-material/AddRounded";

import { TYPOGRAPHY } from "../../theme/typography";

export default function DashboardHeader({
  title,
  description,
  buttonLabel,
  onButtonClick,
}) {
  return (
    <Box
      sx={{
        mb: 4,

        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
      }}
    >
      {/* Left */}

      <Box>
        <Typography sx={TYPOGRAPHY.pageTitle}>
          {title}
        </Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.pageDescription,
            mt: 0.8,
          }}
        >
          {description}
        </Typography>
      </Box>

      {/* Right */}

      <Button
        variant="contained"
        startIcon={<AddRoundedIcon />}
        onClick={onButtonClick}
        sx={{
          height: 46,

          px: 3,

          borderRadius: "14px",

          textTransform: "none",

          boxShadow: "none",

          ...TYPOGRAPHY.formButton,

          "&:hover": {
            boxShadow: "none",
          },
        }}
      >
        {buttonLabel}
      </Button>
    </Box>
  );
}