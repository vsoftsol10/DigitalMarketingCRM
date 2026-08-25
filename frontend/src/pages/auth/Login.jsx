import { Box, Paper, Typography, Divider } from "@mui/material";
import InsightsIcon from "@mui/icons-material/Insights";

import AuthLayout from "../../layouts/AuthLayout";
import LoginForm from "../../components/auth/LoginForm";
import { tokens } from "../../layouts/AuthLayout";

export default function Login() {
  return (
    <AuthLayout>
      <Paper
        elevation={0}
        sx={{
          width: "100%",
          maxWidth: 440,
          mx: "auto",
          p: { xs: 3.5, sm: 5 },
          borderRadius: 3,
          border: "1px solid",
          borderColor: "rgba(0,0,0,0.08)",
          boxShadow: "0 20px 45px -25px rgba(15,20,50,0.25)",
        }}
      >
        <Box
          sx={{
            width: { xs: 44, sm: 48 },
            height: { xs: 44, sm: 48 },
            borderRadius: 2.5,
            bgcolor: tokens.color.primary,
            display: "grid",
            placeItems: "center",
            mb: 3,
          }}
        >
          <InsightsIcon sx={{ color: "#fff", fontSize: { xs: 22, sm: 24 } }} />
        </Box>

        <Typography
          sx={{
            fontFamily: tokens.font.display,
            fontWeight: 700,
            fontSize: { xs: "1.4rem", sm: "1.6rem" },
            color: tokens.color.textPrimary,
            lineHeight: 1.25,
            mb: 0.75,
          }}
        >
          Sign in to your workspace
        </Typography>

        <Typography
          sx={{
            color: tokens.color.textMuted,
            fontSize: { xs: "0.85rem", sm: "0.9rem" },
            mb: 4,
          }}
        >
          Manage every client's social accounts and export insights
          from one place.
        </Typography>

        <LoginForm />

        <Divider sx={{ my: 3.5, borderColor: "rgba(0,0,0,0.06)" }} />

        <Typography
          sx={{
            textAlign: "center",
            fontSize: "0.75rem",
            color: tokens.color.textMuted,
          }}
        >
          © {new Date().getFullYear()} Reach Suite. All rights reserved.
        </Typography>
      </Paper>
    </AuthLayout>
  );
}
