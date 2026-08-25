import { Box, Button, Typography } from "@mui/material";

import DownloadRoundedIcon from "@mui/icons-material/DownloadRounded";

import { TYPOGRAPHY } from "../../theme/typography";

import InsightsFilters from "./InsightsFilters";

export default function InsightsHeader({
  filters,
  onOrganizationChange,
  onPeriodChange,
  onExport,
}) {
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",

        mb: 4,
      }}
    >
      {/* Left */}

      <Box>
        <Typography sx={TYPOGRAPHY.pageTitle}>
          Insights
        </Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.pageDescription,
            mt: 1,
          }}
        >
          View analytics and export performance data.
        </Typography>
      </Box>

      {/* Right */}

      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 2,
        }}
      >
        <InsightsFilters
          filters={filters}
          onOrganizationChange={onOrganizationChange}
          onPeriodChange={onPeriodChange}
        />

        <Button
          variant="outlined"
          startIcon={<DownloadRoundedIcon />}
          onClick={onExport}
          sx={{
            height: 44,

            px: 2.5,

            borderRadius: "14px",

            textTransform: "none",

            borderColor: "#CBD5E1",

            color: "#334155",

            boxShadow: "none",

            "&:hover": {
              borderColor: "#94A3B8",
              bgcolor: "#F8FAFC",
              boxShadow: "none",
            },
          }}
        >
          Export Data
        </Button>
      </Box>
    </Box>
  );
}