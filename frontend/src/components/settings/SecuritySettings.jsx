import {
  Box,
  Divider,
  Paper,
  Typography,
} from "@mui/material";

import LockOutlinedIcon from "@mui/icons-material/LockOutlined";

import PasswordForm from "./PasswordForm";

import { TYPOGRAPHY } from "../../theme/typography";
import { settingsGlassCardSx } from "./settingsGlassSx";

export default function SecuritySettings({
  loading = false,
  error = null,
  onSubmit,
}) {
  return (
    <Paper
      elevation={0}
      sx={{
        ...settingsGlassCardSx,
        overflow: "hidden",
      }}
    >
      {/* ======================================
          SECTION HEADER
      ====================================== */}

      <Box
        sx={{
          px: {
            xs: 2.5,
            sm: 3,
          },

          py: 2.5,
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",

            gap: 1.25,
          }}
        >
          <Box
            sx={{
              width: 38,
              height: 38,

              display: "flex",
              alignItems: "center",
              justifyContent: "center",

              borderRadius: "14px",
              background: "linear-gradient(145deg, rgba(255,255,255,0.96), rgba(235,242,255,0.86))",
              border: "1px solid rgba(255,255,255,0.9)",
              color: "#7650DF",

              flexShrink: 0,
            }}
          >
            <LockOutlinedIcon
              sx={{
                fontSize: 20,
              }}
            />
          </Box>

          <Box
            sx={{
              minWidth: 0,
            }}
          >
            <Typography
              component="h2"
              sx={{
                ...TYPOGRAPHY.cardTitle,

                color: "text.primary",
              }}
            >
              Change Password
            </Typography>

            <Typography
              component="p"
              sx={{
                ...TYPOGRAPHY.bodySmall,

                color: "text.secondary",

                mt: 0.25,
              }}
            >
              Update your account password.
            </Typography>
          </Box>
        </Box>
      </Box>

      <Divider />

      {/* ======================================
          PASSWORD FORM
      ====================================== */}

      <Box
        sx={{
          px: {
            xs: 2.5,
            sm: 3,
          },

          py: 3,
        }}
      >
        <PasswordForm
          loading={loading}
          error={error}
          onSubmit={onSubmit}
        />
      </Box>
    </Paper>
  );
}
