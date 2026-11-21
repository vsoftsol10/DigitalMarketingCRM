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
        mb: 0,
        display: "flex",
        justifyContent: "space-between",
        alignItems: { xs: "stretch", sm: "center" },
        gap: 2,
        flexDirection: { xs: "column", sm: "row" },
      }}
    >
      {/* Left */}

      <Box>
        <Typography
          sx={{
            ...TYPOGRAPHY.pageTitle,
            fontSize: { xs: 30, md: 32 },
            lineHeight: 1.15,
            color: "#172554",
          }}
        >
          {title}
        </Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.pageDescription,
            mt: 0.8,
            color: "#64748B",
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
          height: 48,
          px: 2.5,
          borderRadius: "14px",

          textTransform: "none",

          border: "1px solid transparent",
          background: "linear-gradient(110deg, #8B4BF5 0%, #3977F6 100%)",
          boxShadow: "0 5px 12px rgba(83,75,196,.18)",

          ...TYPOGRAPHY.formButton,

          "&:hover": {
            background: "linear-gradient(110deg, #7D3CEB 0%, #2F6EEA 100%)",
            boxShadow: "0 7px 15px rgba(83,75,196,.23)",
          },
        }}
      >
        {buttonLabel}
      </Button>
    </Box>
  );
}
