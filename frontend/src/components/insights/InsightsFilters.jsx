import {
  Box,
  FormControl,
  MenuItem,
  Select,
  Typography,
} from "@mui/material";
import CalendarMonthOutlinedIcon from "@mui/icons-material/CalendarMonthOutlined";
import FilterAltOutlinedIcon from "@mui/icons-material/FilterAltOutlined";
import PersonOutlineRoundedIcon from "@mui/icons-material/PersonOutlineRounded";
import { insightsGlassControlSx } from "./insightsGlassSx";

const CONTROL_SX = {
  width: "100%",
  minWidth: 0,
  height: 40,
  ...insightsGlassControlSx,
  borderRadius: 999,
  color: "#203965",
  fontSize: 13,
  "& .MuiOutlinedInput-notchedOutline": { borderColor: "transparent" },
  "&:hover .MuiOutlinedInput-notchedOutline": { borderColor: "#AFC8F0" },
  "&.Mui-focused .MuiOutlinedInput-notchedOutline": { borderColor: "#79A8F6", borderWidth: 1 },
  "& .MuiSelect-select": {
    display: "flex",
    alignItems: "center",
    gap: 1,
    py: 1,
    pr: "32px !important",
    overflow: "hidden",
  },
  "& .MuiSelect-icon": { right: 8, color: "#607AA5" },
};

const MENU_PROPS = {
  PaperProps: {
    sx: {
      mt: 0.7,
      border: "1px solid rgba(255,255,255,0.96)",
      borderRadius: 2.5,
      background: "linear-gradient(145deg, rgba(255,255,255,0.98), rgba(233,243,255,0.98))",
      boxShadow: "0 14px 30px rgba(58,94,155,0.18), inset 0 1px 0 #FFFFFF",
      "& .MuiMenuItem-root.Mui-selected": { bgcolor: "rgba(205,224,255,0.76)" },
      "& .MuiMenuItem-root:hover": { bgcolor: "rgba(221,235,255,0.8)" },
    },
  },
};

function LabeledValue({ icon, children }) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1, minWidth: 0 }}>
      {icon}
      <Typography component="span" noWrap sx={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", fontSize: 13 }}>{children}</Typography>
    </Box>
  );
}

export default function InsightsFilters({
  organizations,
  organizationId,
  organizationsLoading,
  duration,
  platform,
  accountId,
  accounts,
  onOrganizationChange,
  onDurationChange,
  onPlatformChange,
  onAccountChange,
}) {
  const platforms = [...new Set(accounts.map((account) => String(account.platform).toLowerCase()))]
    .filter((value) => ["instagram", "facebook"].includes(value));
  const filteredAccounts = platform
    ? accounts.filter((account) => String(account.platform).toLowerCase() === platform)
    : accounts;
  const durationOptions = platform === "facebook"
    ? [{ value: "7D", label: "Last 7 Days" }, { value: "28D", label: "Last 28 Days" }]
    : platform === "instagram"
      ? [{ value: "7D", label: "Last 7 Days" }, { value: "30D", label: "Last 30 Days" }]
      : [];

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: { xs: "stretch", xl: "flex-end" },
        flexWrap: { xs: "wrap", xl: "nowrap" },
        gap: { xs: 1, xl: 0.5 },
        width: { xs: "100%", xl: "auto" },
        flex: { xs: "1 1 100%", xl: "0 0 auto" },
        minWidth: 0,
      }}
    >
      <FormControl size="small" sx={{ flex: { xs: "1 1 calc(50% - 8px)", sm: "1 1 calc(50% - 8px)", xl: "0 0 172px" }, minWidth: 0 }}>
        <Select
          value={organizationId}
          onChange={(event) => onOrganizationChange(event.target.value)}
          disabled={organizationsLoading}
          displayEmpty
          inputProps={{ "aria-label": "Organization" }}
          MenuProps={MENU_PROPS}
          sx={CONTROL_SX}
        >
          <MenuItem value="">Organization</MenuItem>
          {organizations.map((organization) => (
            <MenuItem key={organization.id} value={String(organization.id)}>
              {organization.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ flex: { xs: "1 1 calc(50% - 8px)", sm: "1 1 calc(50% - 8px)", xl: "0 0 120px" }, minWidth: 0 }}>
        <Select
          value={platform}
          onChange={(event) => onPlatformChange(event.target.value)}
          disabled={!organizationId}
          displayEmpty
          inputProps={{ "aria-label": "Platform filter" }}
          MenuProps={MENU_PROPS}
          sx={CONTROL_SX}
          renderValue={(value) => (
            <LabeledValue icon={<FilterAltOutlinedIcon sx={{ color: "#647A9A", fontSize: 17 }} />}>
              {value ? value[0].toUpperCase() + value.slice(1) : "Platform"}
            </LabeledValue>
          )}
        >
          <MenuItem value="">Platform</MenuItem>
          {platforms.map((value) => (
            <MenuItem key={value} value={value}>{value[0].toUpperCase() + value.slice(1)}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl
        size="small"
        disabled={!platform || !filteredAccounts.length}
        sx={{ flex: { xs: "1 1 calc(50% - 8px)", sm: "1 1 calc(50% - 8px)", xl: "0 0 166px" }, minWidth: 0 }}
      >
        <Select
          value={accountId}
          onChange={(event) => onAccountChange(event.target.value)}
          displayEmpty
          inputProps={{ "aria-label": "Connected account" }}
          MenuProps={MENU_PROPS}
          sx={CONTROL_SX}
          renderValue={(value) => {
            const selected = filteredAccounts.find((account) => String(account.id) === value);
            return (
              <LabeledValue icon={<PersonOutlineRoundedIcon sx={{ color: "#647A9A", fontSize: 17 }} />}>
                {selected?.display_name || selected?.username || selected?.account_name || "Connected account"}
              </LabeledValue>
            );
          }}
        >
          <MenuItem value="">Connected account</MenuItem>
          {filteredAccounts.map((account) => (
            <MenuItem key={account.id} value={String(account.id)}>
              {account.display_name || account.username || account.account_name || account.platform_account_id}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl size="small" disabled={!accountId || !durationOptions.length} sx={{ flex: { xs: "1 1 calc(50% - 8px)", sm: "1 1 calc(50% - 8px)", xl: "0 0 136px" }, minWidth: 0 }}>
        <Select
          value={duration}
          onChange={(event) => onDurationChange(event.target.value)}
          displayEmpty
          inputProps={{ "aria-label": "Insights duration" }}
          MenuProps={MENU_PROPS}
          sx={CONTROL_SX}
          renderValue={(value) => (
            <LabeledValue icon={<CalendarMonthOutlinedIcon sx={{ color: "#647A9A", fontSize: 17 }} />}>
              {durationOptions.find((option) => option.value === value)?.label || "Duration"}
            </LabeledValue>
          )}
        >
          <MenuItem value="">Duration</MenuItem>
          {durationOptions.map((option) => (
            <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
}
