import { Grid } from "@mui/material";

export default function InsightsChartsLayout({
  reachChart,
  platformMix,
  bestTime,
  engagementType,
}) {
  return (
    <Grid container spacing={3}>
      {/* First Row */}

      <Grid
        size={{
          xs: 12,
          lg: 8,
        }}
      >
        {reachChart}
      </Grid>

      <Grid
        size={{
          xs: 12,
          lg: 4,
        }}
      >
        {platformMix}
      </Grid>

      {/* Second Row */}

      <Grid
        size={{
          xs: 12,
          lg: 6,
        }}
      >
        {bestTime}
      </Grid>

      <Grid
        size={{
          xs: 12,
          lg: 6,
        }}
      >
        {engagementType}
      </Grid>
    </Grid>
  );
}