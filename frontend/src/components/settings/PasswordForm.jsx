import {
  Alert,
  Box,
  Button,
  Grid,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
} from "@mui/material";

import VisibilityRoundedIcon from "@mui/icons-material/VisibilityRounded";
import VisibilityOffRoundedIcon from "@mui/icons-material/VisibilityOffRounded";
import LockRoundedIcon from "@mui/icons-material/LockRounded";

import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { TYPOGRAPHY } from "../../theme/typography";

const DEFAULT_VALUES = {
  current_password: "",
  new_password: "",
  confirm_password: "",
};

export default function PasswordForm({
  loading = false,
  error = null,
  onSubmit,
}) {
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);

  const [showNewPassword, setShowNewPassword] = useState(false);

  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const { control, handleSubmit, watch, reset } = useForm({
    defaultValues: DEFAULT_VALUES,
    mode: "onSubmit",
  });

  const newPassword = watch("new_password");

  // ==========================================
  // API ERROR
  // ==========================================

  // const getFieldError = (field) => {
  //   if (!error || typeof error !== "object") {
  //     return undefined;
  //   }

  //   const value = error[field];

  //   if (Array.isArray(value)) {
  //     return value[0];
  //   }

  //   return value;
  // };
  const getFieldError = (field) => {
    if (!error || typeof error !== "object") {
      return undefined;
    }

    const value = error[field];

    if (Array.isArray(value)) {
      return value[0];
    }

    if (typeof value === "string") {
      return value;
    }

    return undefined;
  };

  const getGeneralError = () => {
    if (!error || typeof error !== "object") {
      return undefined;
    }

    const value = error.non_field_errors;

    if (Array.isArray(value)) {
      return value[0];
    }

    if (typeof value === "string") {
      return value;
    }

    return undefined;
  };

  // ==========================================
  // SUBMIT
  // ==========================================

  async function handleFormSubmit(data) {
    const result = await onSubmit?.(data);

    if (result?.success) {
      reset(DEFAULT_VALUES);
    }
  }
  // ==========================================
  // PASSWORD FIELD STYLE
  // ==========================================

  const passwordFieldSx = {
    "& .MuiOutlinedInput-root": {
      minHeight: 48,

      borderRadius: 2,

      bgcolor: "background.paper",
    },

    "& .MuiInputLabel-root": {
      ...TYPOGRAPHY.inputLabel,
    },

    "& .MuiInputBase-input": {
      ...TYPOGRAPHY.body,
    },
  };

  return (
    <Box component="form" onSubmit={handleSubmit(handleFormSubmit)} noValidate>
      <Stack spacing={3}>
        {/* ======================================
            API ERROR
        ====================================== */}

        {/* {error && typeof error === "string" && (
          <Alert severity="error">{error}</Alert>
        )} */}
        {(typeof error === "string" || getGeneralError()) && (
          <Alert
            severity="error"
            sx={{
              borderRadius: 2,
            }}
          >
            {typeof error === "string" ? error : getGeneralError()}
          </Alert>
        )}

        {/* ======================================
            CURRENT PASSWORD
        ====================================== */}

        <Controller
          name="current_password"
          control={control}
          rules={{
            required: "Current password is required.",
          }}
          render={({ field, fieldState }) => (
            <TextField
              {...field}
              fullWidth
              type={showCurrentPassword ? "text" : "password"}
              label="Current password"
              autoComplete="current-password"
              error={!!fieldState.error || !!getFieldError("current_password")}
              helperText={
                fieldState.error?.message || getFieldError("current_password")
              }
              disabled={loading}
              sx={passwordFieldSx}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <LockRoundedIcon
                        sx={{
                          fontSize: 19,
                          color: "text.secondary",
                        }}
                      />
                    </InputAdornment>
                  ),

                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        type="button"
                        edge="end"
                        aria-label={
                          showCurrentPassword
                            ? "Hide current password"
                            : "Show current password"
                        }
                        onClick={() =>
                          setShowCurrentPassword((current) => !current)
                        }
                      >
                        {showCurrentPassword ? (
                          <VisibilityOffRoundedIcon />
                        ) : (
                          <VisibilityRoundedIcon />
                        )}
                      </IconButton>
                    </InputAdornment>
                  ),
                },
              }}
            />
          )}
        />

        {/* ======================================
            NEW + CONFIRM PASSWORD
        ====================================== */}

        <Grid container spacing={2.5}>
          {/* NEW PASSWORD */}

          <Grid
            size={{
              xs: 12,
              sm: 6,
            }}
          >
            <Controller
              name="new_password"
              control={control}
              rules={{
                required: "New password is required.",

                minLength: {
                  value: 8,
                  message: "Password must be at least 8 characters.",
                },
              }}
              render={({ field, fieldState }) => (
                <TextField
                  {...field}
                  fullWidth
                  type={showNewPassword ? "text" : "password"}
                  label="New password"
                  autoComplete="new-password"
                  error={!!fieldState.error || !!getFieldError("new_password")}
                  helperText={
                    fieldState.error?.message || getFieldError("new_password")
                  }
                  disabled={loading}
                  sx={passwordFieldSx}
                  slotProps={{
                    input: {
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            type="button"
                            edge="end"
                            aria-label={
                              showNewPassword
                                ? "Hide new password"
                                : "Show new password"
                            }
                            onClick={() =>
                              setShowNewPassword((current) => !current)
                            }
                          >
                            {showNewPassword ? (
                              <VisibilityOffRoundedIcon />
                            ) : (
                              <VisibilityRoundedIcon />
                            )}
                          </IconButton>
                        </InputAdornment>
                      ),
                    },
                  }}
                />
              )}
            />
          </Grid>

          {/* CONFIRM PASSWORD */}

          <Grid
            size={{
              xs: 12,
              sm: 6,
            }}
          >
            <Controller
              name="confirm_password"
              control={control}
              rules={{
                required: "Please confirm your password.",

                validate: (value) =>
                  value === newPassword || "Passwords do not match.",
              }}
              render={({ field, fieldState }) => (
                <TextField
                  {...field}
                  fullWidth
                  type={showConfirmPassword ? "text" : "password"}
                  label="Confirm new password"
                  autoComplete="new-password"
                  error={
                    !!fieldState.error || !!getFieldError("confirm_password")
                  }
                  helperText={
                    fieldState.error?.message ||
                    getFieldError("confirm_password")
                  }
                  disabled={loading}
                  sx={passwordFieldSx}
                  slotProps={{
                    input: {
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            type="button"
                            edge="end"
                            aria-label={
                              showConfirmPassword
                                ? "Hide confirm password"
                                : "Show confirm password"
                            }
                            onClick={() =>
                              setShowConfirmPassword((current) => !current)
                            }
                          >
                            {showConfirmPassword ? (
                              <VisibilityOffRoundedIcon />
                            ) : (
                              <VisibilityRoundedIcon />
                            )}
                          </IconButton>
                        </InputAdornment>
                      ),
                    },
                  }}
                />
              )}
            />
          </Grid>
        </Grid>

        {/* ======================================
            ACTION
        ====================================== */}

        <Box
          sx={{
            display: "flex",
            justifyContent: "flex-end",
            pt: 0.5,
          }}
        >
          <Button
            type="submit"
            variant="contained"
            disableElevation
            disabled={loading}
            startIcon={<LockRoundedIcon />}
            sx={{
              minWidth: 170,

              height: 44,

              px: 2.5,

              borderRadius: 2,

              ...TYPOGRAPHY.button,
            }}
          >
            {loading ? "Updating..." : "Update password"}
          </Button>
        </Box>
      </Stack>
    </Box>
  );
}
