import { Box, Button, Typography } from "@mui/material";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import { useNavigate } from "react-router-dom";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function CreatePostHeader() {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        mb: 5,
      }}
    >
      {/* Back */}

      <Button
        variant="outlined"
        startIcon={<ArrowBackRoundedIcon />}
        onClick={() => navigate("/planner")}
        sx={{
          mb: 4,

          height: 44,

          px: 2.5,

          borderRadius: "14px",

          borderColor: "#CBD5E1",

          color: "#334155",

          bgcolor: "#FFFFFF",

          ...TYPOGRAPHY.button,

          "&:hover": {
            borderColor: "#94A3B8",
            bgcolor: "#F8FAFC",
          },
        }}
      >
        Content Planner
      </Button>

      {/* Title */}

      <Typography sx={TYPOGRAPHY.pageTitle}>
        Create Post
      </Typography>

      {/* Description */}

      <Typography
        sx={{
          ...TYPOGRAPHY.pageDescription,
          mt: 1,
        }}
      >
        Create, preview, and publish content across multiple social platforms.
      </Typography>
    </Box>
  );
}