import { Grid } from "@mui/material";

import DashboardStatCard from "../../dashboard/DashboardStatCard";

export default function StatsCards({ items = [] }) {
  return (
    <Grid container spacing={3} sx={{ mb: 3 }}>
      {items.map((item) => (
        <Grid
          key={item.title}
          size={{ xs: 12, sm: 6, lg: 3 }}
        >
          <DashboardStatCard
            icon={item.icon}
            value={item.value}
            label={item.title}
            variant="dashboard"
          />
        </Grid>
      ))}
    </Grid>
  );
}
