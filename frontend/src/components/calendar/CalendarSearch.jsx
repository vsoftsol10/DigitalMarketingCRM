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
          md: 240,
          lg: 280,
        },

        "& .MuiOutlinedInput-root": {
          height: 42,

          borderRadius: "12px",

          ...calendarGlassControlSx,

          "& fieldset": {
            borderColor: "#D7DFF0",
          },

          "&:hover fieldset": {
            borderColor:
              "#B8C7E7",
          },

          "&.Mui-focused fieldset": {
            borderColor:
              "#8A72E6",
            borderWidth: 1,
            boxShadow: "0 0 0 3px rgba(111,93,236,0.11)",
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
