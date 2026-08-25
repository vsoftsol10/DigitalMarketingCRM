import {
  FormControl,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";

import { useTheme } from "@mui/material/styles";

import {
  Controller,
  useFormContext,
} from "react-hook-form";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function FormSelect({
  name,
  label,
  required = false,
  options = [],
  placeholder = "Select",
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

          <FormControl
            fullWidth
            error={!!fieldState.error}
          >
            <Select
              {...field}
              displayEmpty
              {...props}
              renderValue={(selected) => {
                if (!selected) {
                  return (
                    <Typography
                      sx={{
                        ...TYPOGRAPHY.body,
                        color:
                          theme.palette.text
                            .disabled,
                      }}
                    >
                      {placeholder}
                    </Typography>
                  );
                }

                const option = options.find(
                  (item) =>
                    item.value === selected
                );

                return (
                  option?.label || selected
                );
              }}
              sx={{
                minHeight: compact ? 48 : 52,

                borderRadius: compact
                  ? 1.5
                  : 1.5,

                bgcolor:
                  theme.palette.background
                    .paper,

                ...TYPOGRAPHY.body,

                "& .MuiOutlinedInput-notchedOutline":
                  {
                    borderColor:
                      theme.palette.divider,
                  },

                "&:hover .MuiOutlinedInput-notchedOutline":
                  {
                    borderColor:
                      theme.palette.text
                        .disabled,
                  },

                "&.Mui-focused .MuiOutlinedInput-notchedOutline":
                  {
                    borderColor:
                      theme.palette.primary
                        .main,
                    borderWidth: 2,
                  },

                "& .MuiSelect-select": {
                  py: compact
                    ? 1.5
                    : 1.75,
                  px: 1.75,
                },
              }}
            >
              <MenuItem value="">
                <em>{placeholder}</em>
              </MenuItem>

              {options.map((option) => (
                <MenuItem
                  key={option.value}
                  value={option.value}
                >
                  {option.label}
                </MenuItem>
              ))}
            </Select>

            {(fieldState.error?.message ||
              helperText) && (
              <Typography
                sx={{
                  ...TYPOGRAPHY.helperText,
                  mt: 0.5,
                }}
              >
                {fieldState.error?.message ||
                  helperText}
              </Typography>
            )}
          </FormControl>
        </Stack>
      )}
    />
  );
}