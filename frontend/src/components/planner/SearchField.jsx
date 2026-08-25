import { InputAdornment, TextField } from "@mui/material";

import SearchRoundedIcon from "@mui/icons-material/SearchRounded";

import { TYPOGRAPHY } from "../../theme/typography";

export default function SearchField({
  value,
  onChange,
  placeholder = "Search content ideas...",
}) {
  return (
    <TextField
      fullWidth
      value={value}
      placeholder={placeholder}
      onChange={(event) => onChange(event.target.value)}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <SearchRoundedIcon
              sx={{
                color: "#94A3B8",
                fontSize: 20,
              }}
            />
          </InputAdornment>
        ),
      }}
      sx={{
        "& .MuiOutlinedInput-root": {
          height: 48,
          borderRadius: "14px",

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

        "& input": TYPOGRAPHY.body,
      }}
    />
  );
}
