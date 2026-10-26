import { Box, Typography } from "@mui/material";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import { useNavigate } from "react-router-dom";

import { TYPOGRAPHY } from "../../../theme/typography";

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
          color: "#64748B",
          px: 1.25,
          py: 0.7,
          borderRadius: "999px",
          background: "linear-gradient(145deg, rgba(255,255,255,.78), rgba(232,241,255,.68))",
          border: "1px solid rgba(255,255,255,.88)",
          boxShadow: "0 3px 9px rgba(76, 102, 148, .08), inset 0 1px 0 #fff",
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
