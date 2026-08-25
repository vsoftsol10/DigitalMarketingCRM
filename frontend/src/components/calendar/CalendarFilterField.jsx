import {
  FormControl,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";

import { TYPOGRAPHY } from "../../theme/typography";

export default function CalendarFilterField({
  label,
  value,
  options = [],
  placeholder = "Select",
  onChange,
}) {
  return (
    <Stack spacing={1}>
      <Typography
        component="label"
        sx={TYPOGRAPHY.inputLabel}
      >
        {label}
      </Typography>

      <FormControl fullWidth>
        <Select
          value={value || ""}
          displayEmpty
          onChange={(event) =>
            onChange?.(event.target.value)
          }
          sx={{
            minHeight: 52,

            borderRadius: 2,

            bgcolor: "background.paper",

            "& .MuiOutlinedInput-notchedOutline": {
              borderColor: "divider",
            },

            "&:hover .MuiOutlinedInput-notchedOutline":
              {
                borderColor: "text.secondary",
              },

            "&.Mui-focused .MuiOutlinedInput-notchedOutline":
              {
                borderColor: "primary.main",
                borderWidth: 2,
              },

            "& .MuiSelect-select": {
              ...TYPOGRAPHY.body,

              display: "flex",

              alignItems: "center",

              minHeight: "52px",

              boxSizing: "border-box",

              py: 0,

              px: 2,
            },
          }}
          renderValue={(selected) => {
            if (!selected) {
              return (
                <Typography
                  sx={{
                    ...TYPOGRAPHY.body,

                    color: "text.secondary",
                  }}
                >
                  {placeholder}
                </Typography>
              );
            }

            const selectedOption =
              options.find(
                (option) =>
                  option.value === selected
              );

            return (
              selectedOption?.label ||
              selected
            );
          }}
        >
          <MenuItem value="">
            <Typography
              sx={TYPOGRAPHY.body}
            >
              {placeholder}
            </Typography>
          </MenuItem>

          {options.map((option) => (
            <MenuItem
              key={option.value}
              value={option.value}
            >
              <Typography
                sx={TYPOGRAPHY.body}
              >
                {option.label}
              </Typography>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Stack>
  );
}