import { Box, Button, CircularProgress, Typography } from "@mui/material";

import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import SaveRoundedIcon from "@mui/icons-material/SaveRounded";

import { useNavigate } from "react-router-dom";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function EditHeader({ loading = false }) {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        maxWidth: "980px",
        mx: "auto",
        mb: 4,

        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        gap: 3,
      }}
    >
      {/* Left */}

      <Box>
        <Box
          onClick={() => {
            if (!loading) {
              navigate(-1);
            }
          }}
          sx={{
            display: "inline-flex",
            alignItems: "center",
            gap: 0.5,

            cursor: loading ? "not-allowed" : "pointer",

            color: "#64748B",

            transition: ".2s",

            opacity: loading ? 0.6 : 1,

            "&:hover": {
              color: loading ? "#64748B" : "#2563EB",
            },
          }}
        >
          <ArrowBackRoundedIcon
            sx={{
              fontSize: 18,
            }}
          />

          <Typography sx={TYPOGRAPHY.breadcrumb}>
            Organization Overview
          </Typography>
        </Box>

        <Typography
          sx={{
            ...TYPOGRAPHY.pageTitle,
            mt: 1.5,
          }}
        >
          Edit Organization
        </Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.pageDescription,
            mt: 1,
            maxWidth: 650,
          }}
        >
          Update organization information, subscription, contact details and
          connected social accounts.
        </Typography>
      </Box>

      {/* Right */}

      <Button
        type="submit"
        variant="contained"
        startIcon={
          loading ? (
            <CircularProgress size={18} color="inherit" />
          ) : (
            <SaveRoundedIcon />
          )
        }
        disabled={loading}
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
        {loading ? "Saving..." : "Save Changes"}
      </Button>
    </Box>
  );
}
