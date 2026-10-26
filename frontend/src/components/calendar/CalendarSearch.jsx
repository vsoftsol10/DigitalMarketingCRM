import {
  InputAdornment,
  TextField,
} from "@mui/material";

import SearchRoundedIcon from "@mui/icons-material/SearchRounded";

import { TYPOGRAPHY } from "../../theme/typography";
import { calendarGlassControlSx } from "./calendarGlassSx";

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
          height: 48,

          borderRadius: 999,

          ...calendarGlassControlSx,

          "& fieldset": {
            borderColor: "transparent",
          },

          "&:hover fieldset": {
            borderColor:
              "rgba(174,198,237,0.95)",
          },

          "&.Mui-focused fieldset": {
            borderColor:
              "#79A8F6",
            borderWidth: 1,
            boxShadow: "0 0 0 3px rgba(91,143,236,0.12), inset 0 1px 0 #FFFFFF",
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
