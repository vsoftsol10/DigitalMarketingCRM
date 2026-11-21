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
        alignItems: { xs: "stretch", sm: "center" },
        gap: 2,
        mb: 3,
        flexDirection: { xs: "column", sm: "row" },
      }}
    >
      <Box>
        <Typography sx={TYPOGRAPHY.pageTitle}>{title}</Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.pageDescription,
            mt: 0.75,
            color: "#64748B",
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
          px: 2.5,
          borderRadius: "14px",
          textTransform: "none",

          ...TYPOGRAPHY.button,

          color: "#FFFFFF",
          background: "linear-gradient(110deg, #8B4BF5 0%, #3977F6 100%)",
          boxShadow: "0 5px 12px rgba(83,75,196,.18)",

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
