import {
  InputAdornment,
  TextField,
} from "@mui/material";

import SearchRoundedIcon from "@mui/icons-material/SearchRounded";

import { TYPOGRAPHY } from "../../theme/typography";

export default function CalendarSearch({
  value = "",
  onChange,
}) {
  return (
    <TextField
      value={value}
      onChange={(event) =>
        onChange?.(event.target.value)
      }
      placeholder="Search posts..."
      size="small"
      fullWidth
      slotProps={{
        input: {
          startAdornment: (
            <InputAdornment position="start">
              <SearchRoundedIcon
                sx={{
                  fontSize: 20,
                  color: "text.secondary",
                }}
              />
            </InputAdornment>
          ),
        },
      }}
      sx={{
        width: {
          xs: "100%",
          md: 250,
          lg: 280,
        },

        "& .MuiOutlinedInput-root": {
          height: 44,

          borderRadius: 2,

          bgcolor: "background.paper",

          "& fieldset": {
            borderColor: "divider",
          },

          "&:hover fieldset": {
            borderColor:
              "text.disabled",
          },

          "&.Mui-focused fieldset": {
            borderColor:
              "primary.main",
            borderWidth: 1,
          },
        },

        "& .MuiInputBase-input": {
          ...TYPOGRAPHY.body,

          "&::placeholder": {
            color: "text.secondary",
            opacity: 1,
          },
        },
      }}
    />
  );
}