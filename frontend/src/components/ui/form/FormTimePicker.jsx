import { Stack, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";

import {
  Controller,
  useFormContext,
} from "react-hook-form";

import { TimePicker } from "@mui/x-date-pickers/TimePicker";

import dayjs from "dayjs";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function FormTimePicker({
  name,
  label,
  required = false,
  helperText,
  compact = false,
  ...props
}) {
  const { control } = useFormContext();
  const theme = useTheme();

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState }) => (
        <Stack spacing={0.75}>
          {label && (
            <Typography sx={TYPOGRAPHY.inputLabel}>
              {label}

              {required && (
                <Typography
                  component="span"
                  sx={{
                    color: theme.palette.error.main,
                    ml: 0.5,
                  }}
                >
                  *
                </Typography>
              )}
            </Typography>
          )}

          <TimePicker
            {...props}
            value={
              field.value
                ? dayjs(
                    `2000-01-01 ${field.value}`
                  )
                : null
            }
            onChange={(value) => {
              field.onChange(
                value
                  ? value.format("HH:mm")
                  : ""
              );
            }}
            slotProps={{
              textField: {
                fullWidth: true,
                error: !!fieldState.error,
                helperText:
                  fieldState.error?.message ||
                  helperText,

                sx: {
                  "& .MuiOutlinedInput-root": {
                    minHeight: compact ? 48 : 56,

                    borderRadius: compact
                      ? 1.5
                      : 2,

                    bgcolor:
                      theme.palette.background
                        .paper,

                    "& fieldset": {
                      borderColor:
                        theme.palette.divider,
                    },

                    "&:hover fieldset": {
                      borderColor:
                        theme.palette.text
                          .disabled,
                    },

                    "&.Mui-focused fieldset": {
                      borderColor:
                        theme.palette.primary
                          .main,
                      borderWidth: 2,
                    },
                  },

                  "& .MuiOutlinedInput-input": {
                    ...TYPOGRAPHY.body,

                    padding: compact
                      ? "12px 14px"
                      : "16px 14px",

                    boxSizing: "border-box",
                  },

                  "& .MuiInputAdornment-root": {
                    mr: compact ? 0.5 : 1,
                  },

                  "& .MuiFormHelperText-root": {
                    ...TYPOGRAPHY.helperText,
                    ml: 0,
                    mt: 0.5,
                  },
                },
              },
            }}
          />
        </Stack>
      )}
    />
  );
}