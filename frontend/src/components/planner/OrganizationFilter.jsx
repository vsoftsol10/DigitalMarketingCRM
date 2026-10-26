import { FormControl, MenuItem, Select } from "@mui/material";

import { TYPOGRAPHY } from "../../theme/typography";

export default function OrganizationFilter({ value, options = [], onChange }) {
  return (
    <FormControl
      sx={{
        minWidth: 240,
        "& .MuiSelect-select": {
          color: "#243957",
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
          borderRadius: "16px",
          background:
            "linear-gradient(145deg, rgba(229,238,252,.88), rgba(255,255,255,.9))",
          boxShadow:
            "inset 0 2px 5px rgba(77,102,145,.07), 0 4px 10px rgba(75,100,145,.07), inset 0 1px 0 rgba(255,255,255,.96)",

          "& .MuiOutlinedInput-notchedOutline": {
            borderColor: "rgba(255,255,255,.96)",
            borderWidth: 1,
          },

          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: "rgba(128,157,202,.5)",
          },

          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: "#8CA9E2",
            borderWidth: 1,
          },

          ...TYPOGRAPHY.body,
        }}
        MenuProps={{
          PaperProps: {
            sx: {
              mt: 1,
              borderRadius: "16px",
              border: "1px solid rgba(255,255,255,.92)",
              background:
                "linear-gradient(145deg, rgba(250,252,255,.98), rgba(235,243,255,.96))",
              boxShadow:
                "0 14px 30px rgba(75,96,151,.16), 0 3px 8px rgba(79,99,154,.08), inset 0 1px 0 rgba(255,255,255,.98)",
              "& .MuiMenuItem-root": {
                minHeight: 42,
                mx: 0.75,
                my: 0.25,
                borderRadius: "10px",
                color: "#243957",
                ...TYPOGRAPHY.body,
                "&:hover": { background: "rgba(226,237,255,.68)" },
                "&.Mui-selected": {
                  background: "rgba(221,233,255,.74)",
                  color: "#355FBC",
                  "&:hover": { background: "rgba(213,228,255,.86)" },
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
