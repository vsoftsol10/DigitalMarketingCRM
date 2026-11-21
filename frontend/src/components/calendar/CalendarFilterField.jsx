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
          MenuProps={{
            PaperProps: {
              sx: {
                mt: 0.75,
                border: "1px solid #DCE3F1",
                borderRadius: "12px",
                background: "#FFFFFF",
                boxShadow: "0 12px 28px rgba(54,76,132,0.14)",
                "& .MuiMenuItem-root.Mui-selected": { bgcolor: "#F1EBFF", color: "#6741D9" },
                "& .MuiMenuItem-root:hover": { bgcolor: "#F8F7FF" },
              },
            },
          }}
          sx={{
            minHeight: 46,

            borderRadius: "12px",

            background: "#FFFFFF",
            boxShadow: "none",

            "& .MuiOutlinedInput-notchedOutline": {
              borderColor: "#D7DFF0",
            },

            "&:hover .MuiOutlinedInput-notchedOutline":
              {
                borderColor: "#B8C7E7",
              },

            "&.Mui-focused .MuiOutlinedInput-notchedOutline":
              {
                borderColor: "#8A72E6",
                borderWidth: 1,
                boxShadow: "0 0 0 3px rgba(111,93,236,0.11)",
              },

            "& .MuiSelect-select": {
              ...TYPOGRAPHY.body,

              display: "flex",

              alignItems: "center",

              minHeight: "46px",

              boxSizing: "border-box",

              py: 0,

              px: 1.75,
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
