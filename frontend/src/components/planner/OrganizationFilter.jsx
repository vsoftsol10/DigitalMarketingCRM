import { FormControl, MenuItem, Select } from "@mui/material";

import { TYPOGRAPHY } from "../../theme/typography";

export default function OrganizationFilter({ value, options = [], onChange }) {
  return (
    <FormControl
      sx={{
        minWidth: 240,
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
          borderRadius: "14px",

          "& .MuiOutlinedInput-notchedOutline": {
            borderColor: "#E2E8F0",
          },

          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: "#CBD5E1",
          },

          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: "#2563EB",
            borderWidth: 2,
          },

          ...TYPOGRAPHY.body,
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
