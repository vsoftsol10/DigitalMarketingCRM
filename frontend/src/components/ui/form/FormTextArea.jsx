import {
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import {
  Controller,
  useFormContext,
} from "react-hook-form";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function FormTextArea({
  name,
  label,
  required = false,
  placeholder = "",
  helperText,
  rows = 4,
  ...props
}) {
  const { control } = useFormContext();

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState }) => (
        <Stack spacing={1}>
          {label && (
            <Typography sx={TYPOGRAPHY.inputLabel}>
              {label}

              {required && (
                <Typography
                  component="span"
                  sx={{
                    color: "#EF4444",
                    ml: 0.5,
                  }}
                >
                  *
                </Typography>
              )}
            </Typography>
          )}

          <TextField
            {...field}
            fullWidth
            multiline
            rows={rows}
            placeholder={placeholder}
            error={!!fieldState.error}
            helperText={
              fieldState.error?.message ||
              helperText
            }
            {...props}
            sx={{
              "& .MuiOutlinedInput-root": {
                borderRadius: "12px",
                bgcolor: "#FFFFFF",

                "& fieldset": {
                  borderColor: "#E2E8F0",
                },

                "&:hover fieldset": {
                  borderColor: "#CBD5E1",
                },

                "&.Mui-focused fieldset": {
                  borderColor: "#2563EB",
                  borderWidth: 2,
                },
              },

              "& textarea": TYPOGRAPHY.body,

              "& .MuiFormHelperText-root": {
                ...TYPOGRAPHY.helperText,
                ml: 0,
              },
            }}
          />
        </Stack>
      )}
    />
  );
}