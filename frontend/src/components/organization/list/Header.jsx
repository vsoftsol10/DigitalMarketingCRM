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
        mb: 3.5,
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
          background: "linear-gradient(115deg, #9B72EE 0%, #4B8DEB 100%)",
          border: "1px solid rgba(255,255,255,.72)",
          boxShadow: "0 8px 18px rgba(83, 105, 196, .24), inset 0 1px 0 rgba(255,255,255,.42)",

          "&:hover": {
            background: "linear-gradient(115deg, #8C63E1 0%, #397DE0 100%)",
            boxShadow: "0 10px 22px rgba(83, 105, 196, .28), inset 0 1px 0 rgba(255,255,255,.46)",
          },
        }}
      >
        {buttonLabel}
      </Button>
    </Box>
  );
}
