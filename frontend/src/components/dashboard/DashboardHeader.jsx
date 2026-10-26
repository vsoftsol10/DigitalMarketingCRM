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
            fontSize: { xs: 30, md: 38 },
            lineHeight: 1.15,
            color: "#17284D",
          }}
        >
          {title}
        </Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.pageDescription,
            mt: 0.8,
            color: "#71809F",
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
          px: 2.8,
          borderRadius: "17px",

          textTransform: "none",

          border: "1px solid rgba(255,255,255,.7)",
          background: "linear-gradient(115deg, #A96BEA 0%, #7074ED 54%, #4A91ED 100%)",
          boxShadow: "0 11px 22px rgba(100,92,203,.3), 0 3px 7px rgba(65,101,210,.17), inset 0 1px 0 rgba(255,255,255,.46), inset 0 -2px 3px rgba(67,71,163,.16)",

          ...TYPOGRAPHY.formButton,

          "&:hover": {
            background: "linear-gradient(115deg, #9D60E3 0%, #5E70E8 56%, #3D8FEA 100%)",
            boxShadow: "0 13px 24px rgba(100,92,203,.34), 0 3px 8px rgba(65,101,210,.2), inset 0 1px 0 rgba(255,255,255,.42)",
          },
        }}
      >
        {buttonLabel}
      </Button>
    </Box>
  );
}
