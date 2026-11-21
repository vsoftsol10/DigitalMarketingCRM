import {
  Box,
  Paper,
  Typography,
} from "@mui/material";

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
          px: { xs: 2, sm: 3 },
          pt: { xs: 2, sm: 2.5 },
          pb: 0,
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",

            gap: 0,
          }}
        >
          <Box
            sx={{
              minWidth: 0,
            }}
          >
            <Typography
              component="h2"
              sx={{
                ...TYPOGRAPHY.cardTitle,

                color: "#172554",
                fontSize: { xs: 18, sm: 20 },
                fontWeight: 700,
              }}
            >
              Change Password
            </Typography>

            <Typography
              component="p"
              sx={{
                ...TYPOGRAPHY.bodySmall,

                color: "#667792",

                mt: 0.25,
              }}
            >
              Update your account password.
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* ======================================
          PASSWORD FORM
      ====================================== */}

      <Box
        sx={{
          px: { xs: 2, sm: 3 },
          pt: 2,
          pb: { xs: 2, sm: 2.5 },
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
