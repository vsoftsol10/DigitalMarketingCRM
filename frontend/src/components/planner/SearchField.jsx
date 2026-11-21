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
          borderRadius: "12px",
          background: "#FFFFFF",
          boxShadow: "none",

          "& fieldset": {
            borderColor: "#DCE2EF",
            borderWidth: 1,
          },

          "&:hover fieldset": {
            borderColor: "#B8C3D8",
          },

          "&.Mui-focused fieldset": {
            borderColor: "#7B61E8",
            borderWidth: 1,
          },
        },

        "& .MuiInputAdornment-root": { mr: 0.5 },
        "& input": {
          ...TYPOGRAPHY.body,
          color: "#334155",
          py: 0,
          "&::placeholder": { color: "#94A3B8", opacity: 1 },
        },
      }}
    />
  );
}
