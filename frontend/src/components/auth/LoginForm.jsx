import { useState } from "react";

import {
  Alert,
  Box,
  Button,
  CircularProgress,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
} from "@mui/material";

import {
  Visibility,
  VisibilityOff,
  MailOutlineRounded,
  LockOutlineRounded,
  ShieldOutlined,
} from "@mui/icons-material";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { loginSchema } from "../../validation/auth.schema";
import { useLogin } from "../../hooks/useAuth";
import { tokens } from "../../layouts/AuthLayout";

export default function LoginForm() {
  const [showPassword, setShowPassword] = useState(false);

  const loginMutation = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = (data) => {
    loginMutation.mutate(data);
  };

  const isSubmitting = loginMutation.isPending;

  return (
    <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
      {loginMutation.isError && (
        <Alert
          severity="error"
          sx={{
            mb: 3,
            borderRadius: 2,
            fontSize: "0.875rem",
          }}
        >
          {loginMutation.error?.response?.data?.message ||
            "Couldn't sign you in. Check your email and password and try again."}
        </Alert>
      )}

      <Stack spacing={2.75}>
        <TextField
          label="Work email"
          type="email"
          fullWidth
          autoFocus
          autoComplete="email"
          disabled={isSubmitting}
          {...register("email")}
          error={!!errors.email}
          helperText={errors.email?.message}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <MailOutlineRounded sx={{ fontSize: 20, color: tokens.color.textMuted }} />
              </InputAdornment>
            ),
          }}
          sx={{
            "& .MuiOutlinedInput-root": {
              borderRadius: 2,
              fontSize: "0.95rem",
              bgcolor: "#fff",
            },
            "& .MuiInputLabel-root": { fontSize: "0.9rem" },
          }}
        />

        <TextField
          label="Password"
          type={showPassword ? "text" : "password"}
          fullWidth
          autoComplete="current-password"
          disabled={isSubmitting}
          {...register("password")}
          error={!!errors.password}
          helperText={errors.password?.message}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <LockOutlineRounded sx={{ fontSize: 20, color: tokens.color.textMuted }} />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  onClick={() => setShowPassword((prev) => !prev)}
                  edge="end"
                  disabled={isSubmitting}
                  size="small"
                >
                  {showPassword ? (
                    <VisibilityOff sx={{ fontSize: 20 }} />
                  ) : (
                    <Visibility sx={{ fontSize: 20 }} />
                  )}
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{
            "& .MuiOutlinedInput-root": {
              borderRadius: 2,
              fontSize: "0.95rem",
              bgcolor: "#fff",
            },
            "& .MuiInputLabel-root": { fontSize: "0.9rem" },
          }}
        />

        <Button
          type="submit"
          variant="contained"
          size="large"
          fullWidth
          disabled={isSubmitting}
          startIcon={
            isSubmitting ? <CircularProgress size={18} color="inherit" /> : null
          }
          sx={{
            mt: 1,
            py: 1.4,
            borderRadius: 2,
            fontWeight: 600,
            textTransform: "none",
            fontSize: "0.975rem",
            boxShadow: "none",
            bgcolor: tokens.color.primary,
            "&:hover": {
              bgcolor: "#4A3FD1",
              boxShadow: "0 8px 20px -8px rgba(91,79,233,0.55)",
            },
          }}
        >
          {isSubmitting ? "Signing in\u2026" : "Sign in to dashboard"}
        </Button>

        <Stack
          direction="row"
          alignItems="center"
          justifyContent="center"
          spacing={0.75}
          sx={{ pt: 0.5, color: tokens.color.textMuted }}
        >
          <ShieldOutlined sx={{ fontSize: 15 }} />
          <Box component="span" sx={{ fontSize: "0.75rem" }}>
            Secured with encrypted authentication
          </Box>
        </Stack>
      </Stack>
    </Box>
  );
}