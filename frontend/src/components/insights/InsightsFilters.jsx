import {
  Box,
  FormControl,
  MenuItem,
  Select,
  ToggleButton,
  ToggleButtonGroup,
} from "@mui/material";

export default function InsightsFilters({
  filters,
  onOrganizationChange,
  onPeriodChange,
}) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 2,
      }}
    >
      {/* Organization */}

      <FormControl size="small">
        <Select
          value={filters.organization}
          onChange={(event) => onOrganizationChange(event.target.value)}
          sx={{
            minWidth: 190,
            height: 44,

            borderRadius: "14px",

            bgcolor: "#FFFFFF",

            "& .MuiOutlinedInput-notchedOutline": {
              borderColor: "#CBD5E1",
            },

            "&:hover .MuiOutlinedInput-notchedOutline": {
              borderColor: "#94A3B8",
            },
          }}
        >
          <MenuItem value="all">All organizations</MenuItem>

          {/* Later backend */}
        </Select>
      </FormControl>

      {/* Period */}

      <ToggleButtonGroup
        exclusive
        value={filters.period}
        onChange={(_, value) => {
          if (value) {
            onPeriodChange(value);
          }
        }}
        sx={{
          gap: 0.5,

          "& .MuiToggleButton-root": {
            border: "none",

            borderRadius: "10px",

            px: 2,

            height: 44,

            textTransform: "none",

            fontWeight: 600,

            color: "#64748B",

            "&.Mui-selected": {
              bgcolor: "#EEF4FF",
              color: "#2563EB",

              "&:hover": {
                bgcolor: "#EEF4FF",
              },
            },

            "&:hover": {
              bgcolor: "#F8FAFC",
            },
          },
        }}
      >
        <ToggleButton value="7D">7D</ToggleButton>

        <ToggleButton value="30D">30D</ToggleButton>

        <ToggleButton value="90D">90D</ToggleButton>
      </ToggleButtonGroup>
    </Box>
  );
}
