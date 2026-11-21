import { Box, Typography } from "@mui/material";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import { useNavigate } from "react-router-dom";

import { TYPOGRAPHY } from "../../../theme/typography";
import { organizationSecondaryButtonSx } from "../organizationUiSx";

export default function CreateHeader() {
  const navigate = useNavigate();

  return (
    <Box sx={{ width: "100%", maxWidth: "980px", mx: "auto", mb: 4 }}>
      {/* Back */}

      <Box
        onClick={() => navigate("/organizations")}
        sx={{
          display: "inline-flex",
          alignItems: "center",
          gap: 0.5,
          cursor: "pointer",
          ...organizationSecondaryButtonSx,
          minHeight: 36,
          px: 1.25,
          py: 0.5,
          color: "#64748B",
          transition: "0.2s",

          "&:hover": {
            color: "#4E73C8",
          },
        }}
      >
        <ArrowBackRoundedIcon
          sx={{
            fontSize: 18,
          }}
        />

        <Typography sx={TYPOGRAPHY.breadcrumb}>
          Organizations
        </Typography>
      </Box>

      {/* Title */}

      <Typography
        sx={{
          ...TYPOGRAPHY.pageTitle,
          mt: 2,
        }}
      >
        Create Organization
      </Typography>

      {/* Description */}

      <Typography
        sx={{
          ...TYPOGRAPHY.pageDescription,
          mt: 1,
        }}
      >
        Add a new client to your agency roster
      </Typography>
    </Box>
  );
}
