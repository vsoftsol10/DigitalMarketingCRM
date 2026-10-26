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
                color: "#647D9F",
                fontSize: 22,
              }}
            />
          </InputAdornment>
        ),
      }}
      sx={{
        "& .MuiOutlinedInput-root": {
          height: 48,
          borderRadius: "999px",
          background:
            "linear-gradient(145deg, rgba(229,238,252,.82), rgba(255,255,255,.9))",
          boxShadow:
            "inset 0 2px 6px rgba(77,102,145,.09), 0 3px 8px rgba(75,100,145,.06), inset 0 1px 0 rgba(255,255,255,.96)",

          "& fieldset": {
            borderColor: "rgba(255,255,255,.96)",
            borderWidth: 1,
          },

          "&:hover fieldset": {
            borderColor: "rgba(128,157,202,.48)",
          },

          "&.Mui-focused fieldset": {
            borderColor: "#8CA9E2",
            borderWidth: 1,
          },
        },

        "& .MuiInputAdornment-root": { mr: 0.5 },
        "& input": {
          ...TYPOGRAPHY.body,
          color: "#243957",
          py: 0,
          "&::placeholder": { color: "#7185A2", opacity: 0.78 },
        },
      }}
    />
  );
}
