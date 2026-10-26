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
import overviewGlassCardSx from "../overview/overviewGlassCardSx";

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
        ...overviewGlassCardSx,
        mt: 0,
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          px: { xs: 2, md: 3 },
          py: { xs: 1.75, md: 2 },
          borderBottom: "1px solid rgba(162,181,210,.26)",
          gap: { xs: 1.5, md: 3 },
          flexWrap: { xs: "wrap", md: "nowrap" },
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
            maxWidth: 820,
            minWidth: { xs: "100%", md: 0 },
            flex: "1 1 auto",

            "& .MuiOutlinedInput-root": {
              height: 50,
              borderRadius: "999px",
              background: "linear-gradient(145deg, rgba(229,238,252,.82), rgba(255,255,255,.9))",
              boxShadow: "inset 0 2px 6px rgba(77,102,145,.09), 0 3px 8px rgba(75,100,145,.06), inset 0 1px 0 rgba(255,255,255,.96)",
              "& fieldset": { borderColor: "rgba(255,255,255,.96)" },
              "&:hover fieldset": { borderColor: "rgba(128,157,202,.48)" },
              "&.Mui-focused fieldset": { borderColor: "#8CA9E2", borderWidth: 1 },
            },
            "& .MuiInputAdornment-root": { mr: 0.5 },
            "& .MuiInputAdornment-root svg": { color: "#647D9F", fontSize: 22 },

            "& input": {
              ...TYPOGRAPHY.body,
              color: "#243957",
              py: 0,
              "&::placeholder": { color: "#7185A2", opacity: 0.78 },
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
            "& .MuiTabs-indicator": { display: "none" },
            "& .MuiTabs-flexContainer": { gap: { xs: 0, sm: 0.5 } },
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
                borderRadius: "999px",
                textTransform: "none",
                color: "#607493",
                transition: "background-color .18s ease, box-shadow .18s ease, color .18s ease",

                ...TYPOGRAPHY.body,

                "&:hover": {
                  background: "rgba(226,237,255,.62)",
                  color: "#405F91",
                },
                "&.Mui-focusVisible": {
                  outline: "2px solid rgba(111,145,211,.55)",
                  outlineOffset: 2,
                },

                "&.Mui-selected": {
                  color: "#355FBC",
                  fontWeight: 600,
                  background: "linear-gradient(145deg, #EEE8FF, #F7F8FF)",
                  border: "1px solid rgba(255,255,255,.96)",
                  boxShadow: "0 5px 11px rgba(95,91,164,.14), 0 2px 5px rgba(78,107,165,.08), inset 0 1px 0 #fff, inset 0 -1px 2px rgba(125,136,184,.08)",
                  "&:hover": {
                    background: "linear-gradient(145deg, #E9E1FF, #F5F7FF)",
                  },
                },
              }}
            />
          ))}
        </Tabs>
      </Box>

      {/* Organization Grid will render here */}
      <Box
        sx={{
          p: { xs: 2, md: 3 },
          background: "linear-gradient(180deg, rgba(241,247,255,.58), rgba(255,255,255,.3))",
        }}
      >
        {children}
      </Box>
    </Paper>
  );
}
