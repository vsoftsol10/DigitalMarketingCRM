import { Grid } from "@mui/material";
import InsightStatCard from "./InsightStatCard";

const ITEMS = [
  { key: "reach", title: "Total Reach" },
  { key: "engagement", title: "Total Engagement" },
  { key: "followers", title: "Total Followers" },
  { key: "views", title: "Total Views" },
];

export default function InsightsStats({ metrics = {}, loading = false, selected = false }) {
  return (
    <Grid container spacing={1.75}>
      {ITEMS.map((item) => (
        <Grid key={item.key} size={{ xs: 12, sm: 6, lg: 3 }}>
          <InsightStatCard
            metricKey={item.key}
            title={item.title}
            metric={metrics[item.key]}
            loading={loading}
            selected={selected}
          />
        </Grid>
      ))}
    </Grid>
  );
}
