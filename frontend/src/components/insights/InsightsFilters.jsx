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

const CONTROL_SX = {
  width: "100%",
  minWidth: 0,
  height: 40,
  bgcolor: "#fff",
  borderRadius: "9px",
  color: "#1E293B",
  fontSize: 13,
  "& .MuiOutlinedInput-notchedOutline": { borderColor: "#DBE4F0" },
  "&:hover .MuiOutlinedInput-notchedOutline": { borderColor: "#A7B8D1" },
  "& .MuiSelect-select": {
    display: "flex",
    alignItems: "center",
    gap: 1,
    py: 1,
    pr: "32px !important",
    overflow: "hidden",
  },
  "& .MuiSelect-icon": { right: 8, color: "#647A9A" },
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
        gap: 1,
        width: { xs: "100%", xl: "auto" },
        flex: "1 1 680px",
        minWidth: 0,
      }}
    >
      <FormControl size="small" sx={{ flex: { xs: "1 1 calc(50% - 8px)", sm: "1 1 calc(50% - 8px)", xl: "0 0 190px" }, minWidth: 0 }}>
        <Select
          value={organizationId}
          onChange={(event) => onOrganizationChange(event.target.value)}
          disabled={organizationsLoading}
          displayEmpty
          inputProps={{ "aria-label": "Organization" }}
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

      <FormControl size="small" sx={{ flex: { xs: "1 1 calc(50% - 8px)", sm: "1 1 calc(50% - 8px)", xl: "0 0 130px" }, minWidth: 0 }}>
        <Select
          value={platform}
          onChange={(event) => onPlatformChange(event.target.value)}
          disabled={!organizationId}
          displayEmpty
          inputProps={{ "aria-label": "Platform filter" }}
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
        sx={{ flex: { xs: "1 1 calc(50% - 8px)", sm: "1 1 calc(50% - 8px)", xl: "0 0 180px" }, minWidth: 0 }}
      >
        <Select
          value={accountId}
          onChange={(event) => onAccountChange(event.target.value)}
          displayEmpty
          inputProps={{ "aria-label": "Connected account" }}
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

      <FormControl size="small" disabled={!accountId || !durationOptions.length} sx={{ flex: { xs: "1 1 calc(50% - 8px)", sm: "1 1 calc(50% - 8px)", xl: "0 0 150px" }, minWidth: 0 }}>
        <Select
          value={duration}
          onChange={(event) => onDurationChange(event.target.value)}
          displayEmpty
          inputProps={{ "aria-label": "Insights duration" }}
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
