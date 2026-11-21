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
import { organizationCardSx } from "../organizationUiSx";

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
        ...organizationCardSx,
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
          borderBottom: "1px solid #E5E9F1",
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
              borderRadius: "12px",
              background: "#F8FAFC",
              boxShadow: "none",
              "& fieldset": { borderColor: "#DCE2EF" },
              "&:hover fieldset": { borderColor: "#B8C3D8" },
              "&.Mui-focused fieldset": { borderColor: "#7B61E8", borderWidth: 1 },
            },
            "& .MuiInputAdornment-root": { mr: 0.5 },
            "& .MuiInputAdornment-root svg": { color: "#647D9F", fontSize: 22 },

            "& input": {
              ...TYPOGRAPHY.body,
              color: "#1E293B",
              py: 0,
              "&::placeholder": { color: "#8491AC", opacity: 1 },
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
                  background: "#F8FAFC",
                  color: "#475569",
                },
                "&.Mui-focusVisible": {
                  outline: "2px solid rgba(111,145,211,.55)",
                  outlineOffset: 2,
                },

                "&.Mui-selected": {
                  color: "#6941D9",
                  fontWeight: 600,
                  background: "#F5F2FF",
                  border: "1px solid #DAD1F8",
                  boxShadow: "none",
                  "&:hover": {
                    background: "#F5F2FF",
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
          background: "#FFFFFF",
        }}
      >
        {children}
      </Box>
    </Paper>
  );
}
