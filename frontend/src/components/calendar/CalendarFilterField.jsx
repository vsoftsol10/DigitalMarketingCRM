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
                border: "1px solid rgba(255,255,255,0.96)",
                borderRadius: 2.5,
                background: "linear-gradient(145deg, rgba(255,255,255,0.98), rgba(233,243,255,0.98))",
                boxShadow: "0 14px 30px rgba(58,94,155,0.18), inset 0 1px 0 #FFFFFF",
                "& .MuiMenuItem-root.Mui-selected": { bgcolor: "rgba(205,224,255,0.78)" },
                "& .MuiMenuItem-root:hover": { bgcolor: "rgba(221,235,255,0.8)" },
              },
            },
          }}
          sx={{
            minHeight: 52,

            borderRadius: 2.5,

            background: "linear-gradient(145deg, rgba(255,255,255,0.97), rgba(232,242,255,0.9))",
            boxShadow: "0 4px 10px rgba(70,106,172,0.09), inset 0 1px 0 #FFFFFF",

            "& .MuiOutlinedInput-notchedOutline": {
              borderColor: "rgba(194,214,246,0.85)",
            },

            "&:hover .MuiOutlinedInput-notchedOutline":
              {
                borderColor: "#AFC8F0",
              },

            "&.Mui-focused .MuiOutlinedInput-notchedOutline":
              {
                borderColor: "#78A5F0",
                borderWidth: 1,
                boxShadow: "0 0 0 3px rgba(91,143,236,0.12)",
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
