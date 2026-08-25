import { Grid } from "@mui/material";

import InsightStatCard from "./InsightStatCard";

export default function InsightsStats({ statistics }) {
  const items = [
    {
      title: "Total Reach",
      value: "2.7M",
      change: statistics.total_reach_change,
      positive: statistics.total_reach_change >= 0,
    },

    {
      title: "Engagement",
      value: "18.1K",
      change: statistics.engagement_change,
      positive: statistics.engagement_change >= 0,
    },

    {
      title: "Avg. Eng. Rate",
      value: "4.9%",
      change: statistics.engagement_rate_change,
      positive: statistics.engagement_rate_change >= 0,
    },

    {
      title: "Followers",
      value: "341.6K",
      change: statistics.followers_change,
      positive: statistics.followers_change >= 0,
    },
  ];

  return (
    <Grid container spacing={3}>
      {items.map((item) => (
        <Grid
          key={item.title}
          size={{
            xs: 12,
            sm: 6,
            lg: 3,
          }}
        >
          <InsightStatCard {...item} />
        </Grid>
      ))}
    </Grid>
  );
}
