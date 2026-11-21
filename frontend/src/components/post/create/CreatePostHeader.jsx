import { Box, Button, Typography } from "@mui/material";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import { useNavigate } from "react-router-dom";

import { TYPOGRAPHY } from "../../../theme/typography";
import { postSecondaryButtonSx } from "./postUiSx";

export default function CreatePostHeader({ showBack = true }) {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        mb: 3,
      }}
    >
      {/* Back */}

      {showBack && <Button
        variant="outlined"
        startIcon={<ArrowBackRoundedIcon />}
        onClick={() => navigate("/planner")}
        sx={{ ...postSecondaryButtonSx, mb: 2, minHeight: 40, ...TYPOGRAPHY.button }}
      >
        Content Planner
      </Button>}

      {/* Title */}

      <Typography sx={{ ...TYPOGRAPHY.pageTitle, color: "#102347", fontSize: { xs: 28, sm: 32 } }}>
        Create Post
      </Typography>

      {/* Description */}

      <Typography
        sx={{
          ...TYPOGRAPHY.pageDescription,
          mt: 1,
          color: "#667792",
        }}
      >
        Create, preview, and publish content across multiple social platforms.
      </Typography>
    </Box>
  );
}
