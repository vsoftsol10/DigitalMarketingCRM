import { useState } from "react";
import { Box, Button, Menu, MenuItem, Typography } from "@mui/material";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import InsightsFilters from "./InsightsFilters";
import { insightsGlassControlSx } from "./insightsGlassSx";

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
        width: "100%",
        minWidth: 0,
        mb: 1,
        display: "grid",
        gridTemplateColumns: {
          xs: "minmax(0, 1fr)",
          lg: "minmax(280px, 1fr) minmax(0, 2fr)",
          xl: "minmax(390px, 1fr) minmax(740px, max-content)",
        },
        alignItems: { xs: "stretch", lg: "center" },
        gap: { xs: 1.5, xl: 0.5 },
      }}
    >
      <Box sx={{ minWidth: 0 }}>
        <Typography sx={{ fontSize: 32, fontWeight: 750, color: "#12264D", lineHeight: 1.15, letterSpacing: "-0.03em" }}>
          Insights
        </Typography>
        <Typography sx={{ mt: 0.65, color: "#647A9B", fontSize: 14.5, lineHeight: 1.5, whiteSpace: { xs: "normal", xl: "nowrap" }, overflowWrap: { xs: "break-word", xl: "normal" } }}>
          Track your social media performance and engagement.
        </Typography>
      </Box>

      <Box sx={{ display: "flex", alignItems: "center", gap: { xs: 1, xl: 0.5 }, width: { xs: "100%", xl: "auto" }, minWidth: 0, justifyContent: { xs: "flex-start", xl: "flex-end" }, flexWrap: { xs: "wrap", xl: "nowrap" } }}>
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
            minWidth: 128,
            height: 44,
            flex: "0 0 auto",
            whiteSpace: "nowrap",
            px: 1.5,
            ...insightsGlassControlSx,
            borderRadius: 999,
            color: "#203965",
            fontSize: 13,
            fontWeight: 650,
            textTransform: "none",
            "& .MuiButton-startIcon": { color: "#607AA5" },
            "&:hover": { borderColor: "#AFC8F0", background: "linear-gradient(145deg, #FFFFFF 0%, #DFECFF 100%)", boxShadow: "0 8px 16px rgba(70,106,172,0.17)" },
            "&.Mui-disabled": { borderColor: "rgba(255,255,255,0.9)", background: "rgba(237,244,254,0.75)", color: "#94A3B8" },
            "&.Mui-disabled .MuiButton-startIcon": { color: "#A8B5C6" },
          }}
        >
          Export
        </Button>
        <Menu
          anchorEl={exportAnchor}
          open={Boolean(exportAnchor)}
          onClose={() => setExportAnchor(null)}
          sx={{
            "& .MuiPaper-root": {
              mt: 0.7,
              border: "1px solid rgba(255,255,255,0.96)",
              borderRadius: 2.5,
              background: "linear-gradient(145deg, rgba(255,255,255,0.98), rgba(233,243,255,0.98))",
              boxShadow: "0 14px 30px rgba(58,94,155,0.18), inset 0 1px 0 #FFFFFF",
            },
          }}
        >
          <MenuItem onClick={() => { setExportAnchor(null); onExportSelect("current"); }}>Export Current Data</MenuItem>
          <MenuItem onClick={() => { setExportAnchor(null); onExportSelect("add_ads"); }}>Add Data &amp; Export</MenuItem>
        </Menu>
      </Box>
    </Box>
  );
}
