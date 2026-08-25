import {
  Box,
  Paper,
  Tabs,
  Tab,
  TextField,
  InputAdornment,
} from "@mui/material";

import SearchRoundedIcon from "@mui/icons-material/SearchRounded";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function SearchTabs({
  search = "",
  onSearchChange,
  activeTab = "all",
  onTabChange,
  counts = {
    all: 0,
    active: 0,
    inactive: 0,
  },
  children,
}) {
  const tabs = [
    {
      label: `All (${counts.all})`,
      value: "all",
    },
    {
      label: `Active (${counts.active})`,
      value: "active",
    },
    {
      label: `Inactive (${counts.inactive})`,
      value: "inactive",
    },
  ];

  return (
    <Paper
      elevation={0}
      sx={{
        mt: 4,
        borderRadius: "20px",
        border: "1px solid #E5E7EB",
        bgcolor: "#FFFFFF",
        overflow: "hidden",
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          px: 3,
          py: 2,
          borderBottom: "1px solid #E5E7EB",
          gap: 3,
        }}
      >
        <TextField
          fullWidth
          placeholder="Search organizations..."
          value={search}
          onChange={(e) => onSearchChange?.(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchRoundedIcon
                  sx={{
                    color: "#94A3B8",
                  }}
                />
              </InputAdornment>
            ),
          }}
          sx={{
            maxWidth: 760,

            "& .MuiOutlinedInput-root": {
              height: 48,
              borderRadius: "14px",
            },

            "& input": {
              ...TYPOGRAPHY.body,
            },
          }}
        />

        <Tabs
          value={activeTab}
          onChange={(_, value) => onTabChange?.(value)}
          TabIndicatorProps={{
            sx: {
              height: 2,
            },
          }}
          sx={{
            minHeight: 48,
            flexShrink: 0,
          }}
        >
          {tabs.map((tab) => (
            <Tab
              key={tab.value}
              value={tab.value}
              disableRipple
              label={tab.label}
              sx={{
                minHeight: 48,
                minWidth: "auto",
                px: 2,
                textTransform: "none",

                ...TYPOGRAPHY.body,

                "&.Mui-selected": {
                  color: "#2563EB",
                  fontWeight: 600,
                },
              }}
            />
          ))}
        </Tabs>
      </Box>

      {/* Organization Grid will render here */}
      <Box
        sx={{
          p: 3,
        }}
      >
        {children}
      </Box>
    </Paper>
  );
}
