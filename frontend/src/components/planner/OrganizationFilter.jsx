import { FormControl, MenuItem, Select } from "@mui/material";

import { TYPOGRAPHY } from "../../theme/typography";

export default function OrganizationFilter({ value, options = [], onChange }) {
  return (
    <FormControl
      sx={{
        minWidth: { xs: "100%", md: 220 },
        "& .MuiSelect-select": {
          color: "#334155",
          ...TYPOGRAPHY.body,
        },
      }}
    >
      <Select
        value={value}
        displayEmpty
        onChange={(event) => onChange(event.target.value)}
        renderValue={(selected) => {
          if (!selected || selected === "all") {
            return "All Organizations";
          }

          const organization = options.find((item) => item.id === selected);

          return organization?.name || "Organization";
        }}
        sx={{
          height: 48,
          borderRadius: "12px",
          background: "#FFFFFF",
          boxShadow: "none",

          "& .MuiOutlinedInput-notchedOutline": {
            borderColor: "#DCE2EF",
            borderWidth: 1,
          },

          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: "#B8C3D8",
          },

          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: "#7B61E8",
            borderWidth: 1,
          },

          ...TYPOGRAPHY.body,
        }}
        MenuProps={{
          PaperProps: {
            sx: {
              mt: 1,
              border: "1px solid #DDE3F1",
              borderRadius: "12px",
              background: "#FFFFFF",
              boxShadow: "0 12px 28px rgba(31,41,80,.14)",
              "& .MuiMenuItem-root": {
                minHeight: 42,
                mx: 0.75,
                my: 0.25,
                borderRadius: "10px",
                color: "#334155",
                ...TYPOGRAPHY.body,
                "&:hover": { background: "#F5F2FF" },
                "&.Mui-selected": {
                  background: "#F5F2FF",
                  color: "#6941D9",
                  "&:hover": { background: "#F5F2FF" },
                },
                "&.Mui-focusVisible": {
                  outline: "2px solid rgba(111,145,211,.42)",
                  outlineOffset: -2,
                },
              },
            },
          },
        }}
      >
        <MenuItem value="all">All Organizations</MenuItem>

        {options.map((organization) => (
          <MenuItem key={organization.id} value={organization.id}>
            {organization.name}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
