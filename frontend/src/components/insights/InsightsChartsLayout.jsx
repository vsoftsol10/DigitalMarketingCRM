import { Box } from "@mui/material";

export default function InsightsChartsLayout({ followerGrowth, accountPerformance }) {
  return (
    <Box sx={{
      display: "grid",
      gridTemplateColumns: { xs: "minmax(0, 1fr)", lg: "minmax(0, 1.55fr) minmax(0, 1fr)" },
      gap: 1.75,
      width: "100%",
      minWidth: 0,
      alignItems: "stretch",
      "& > *": { width: "100%", minWidth: 0 },
    }}>
      <Box sx={{ minWidth: 0 }}>{followerGrowth}</Box>
      <Box sx={{ minWidth: 0 }}>{accountPerformance}</Box>
    </Box>
  );
}
