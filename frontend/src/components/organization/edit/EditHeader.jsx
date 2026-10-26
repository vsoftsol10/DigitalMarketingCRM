import { Box, Typography } from "@mui/material";

import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import SaveRoundedIcon from "@mui/icons-material/SaveRounded";

import { useNavigate } from "react-router-dom";

import { TYPOGRAPHY } from "../../../theme/typography";
import PrimaryButton from "../../ui/button/PrimaryButton";
import { glassPrimaryButtonSx } from "../../ui/form/glassFormSx";

export default function EditHeader({ loading = false }) {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        width: "100%",
        maxWidth: "980px",
        mx: "auto",
        mb: 4,

        display: "flex",
        flexDirection: { xs: "column", sm: "row" },
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
            px: 1.25,
            py: 0.7,
            borderRadius: "999px",
            background: "linear-gradient(145deg, rgba(255,255,255,.78), rgba(232,241,255,.68))",
            border: "1px solid rgba(255,255,255,.88)",
            boxShadow: "0 3px 9px rgba(76, 102, 148, .08), inset 0 1px 0 #fff",

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
            mt: 2,
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

      <PrimaryButton
        type="submit"
        fullWidth={false}
        loading={loading}
        height={46}
        startIcon={<SaveRoundedIcon />}
        sx={{
          width: { xs: "100%", sm: "auto" },
          px: 3,
          textTransform: "none",
          ...TYPOGRAPHY.formButton,
          ...glassPrimaryButtonSx,
        }}
      >
        {loading ? "Saving..." : "Save Changes"}
      </PrimaryButton>
    </Box>
  );
}
