import { Box, Typography } from "@mui/material";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import { useNavigate } from "react-router-dom";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function EditContentIdeaHeader() {
  const navigate = useNavigate();

  return (
    <Box sx={{ mb: 4 }}>
      {/* Back */}

      <Box
        onClick={() => navigate("/planner")}
        sx={{
          display: "inline-flex",
          alignItems: "center",
          gap: 0.5,
          cursor: "pointer",
          color: "#64748B",
          transition: "0.2s",

          "&:hover": {
            color: "#2563EB",
          },
        }}
      >
        <ArrowBackRoundedIcon
          sx={{
            fontSize: 18,
          }}
        />

        <Typography sx={TYPOGRAPHY.breadcrumb}>Content Planner</Typography>
      </Box>

      {/* Title */}

      <Typography
        sx={{
          ...TYPOGRAPHY.pageTitle,
          mt: 2,
        }}
      >
        Edit Content Idea
      </Typography>

      {/* Description */}

      <Typography
        sx={{
          ...TYPOGRAPHY.pageDescription,
          mt: 1,
        }}
      >
        Update the content idea details before publishing.
      </Typography>
    </Box>
  );
}
