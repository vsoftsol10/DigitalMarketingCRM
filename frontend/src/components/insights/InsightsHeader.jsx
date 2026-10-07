import { useState } from "react";
import { Box, Button, Menu, MenuItem, Typography } from "@mui/material";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import InsightsFilters from "./InsightsFilters";

export default function InsightsHeader({
  organizations,
  organizationId,
  accounts,
  duration,
  platform,
  accountId,
  organizationsLoading,
  exportEnabled,
  onExportSelect,
  onOrganizationChange,
  onDurationChange,
  onPlatformChange,
  onAccountChange,
}) {
  const [exportAnchor, setExportAnchor] = useState(null);

  return (
    <Box
      sx={{
        mb: 1,
        display: "flex",
        alignItems: { xs: "stretch", xl: "center" },
        justifyContent: "space-between",
        flexDirection: { xs: "column", xl: "row" },
        flexWrap: "wrap",
        gap: { xs: 1.5, xl: 2.5 },
      }}
    >
      <Box sx={{ minWidth: 240, flex: "1 1 270px" }}>
        <Typography sx={{ fontSize: 30, fontWeight: 700, color: "#13264A", lineHeight: 1.15 }}>
          Insights
        </Typography>
        <Typography sx={{ mt: 1, color: "#657A9A", fontSize: 14 }}>
          Track your social media performance and engagement.
        </Typography>
      </Box>

      <Box sx={{ display: "flex", alignItems: "center", gap: 1, flex: "1 1 680px", minWidth: 0, justifyContent: { xs: "stretch", xl: "flex-end" }, flexWrap: { xs: "wrap", xl: "nowrap" } }}>
      <InsightsFilters
        organizations={organizations}
        organizationId={organizationId}
        organizationsLoading={organizationsLoading}
        duration={duration}
        platform={platform}
        accountId={accountId}
        accounts={accounts}
        onOrganizationChange={onOrganizationChange}
        onDurationChange={onDurationChange}
        onPlatformChange={onPlatformChange}
        onAccountChange={onAccountChange}
      />
        <Button
          variant="outlined"
          startIcon={<DownloadOutlinedIcon />}
          disabled={!exportEnabled}
          onClick={(event) => setExportAnchor(event.currentTarget)}
          sx={{
            minWidth: 112,
            height: 40,
            flex: "0 0 auto",
            px: 1.5,
            border: "1px solid #DBE4F0",
            borderRadius: "9px",
            bgcolor: "#fff",
            color: "#1E293B",
            fontSize: 13,
            fontWeight: 400,
            textTransform: "none",
            boxShadow: "none",
            "& .MuiButton-startIcon": { color: "#647A9A" },
            "&:hover": { borderColor: "#A7B8D1", bgcolor: "#fff", boxShadow: "none" },
            "&.Mui-disabled": { borderColor: "#DBE4F0", bgcolor: "#fff", color: "#94A3B8" },
            "&.Mui-disabled .MuiButton-startIcon": { color: "#A8B5C6" },
          }}
        >
          Export
        </Button>
        <Menu anchorEl={exportAnchor} open={Boolean(exportAnchor)} onClose={() => setExportAnchor(null)}>
          <MenuItem onClick={() => { setExportAnchor(null); onExportSelect("current"); }}>Export Current Data</MenuItem>
          <MenuItem onClick={() => { setExportAnchor(null); onExportSelect("add_ads"); }}>Add Data &amp; Export</MenuItem>
        </Menu>
      </Box>
    </Box>
  );
}
