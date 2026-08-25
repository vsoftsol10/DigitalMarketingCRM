import { Grid } from "@mui/material";

import PlanCard from "./PlanCard";

export default function PlansGrid({
  plans = [],
  onSelect,
}) {
  return (
    <Grid
      container
      columnSpacing={2}
      rowSpacing={2}
      sx={{
        width: "100%",
        m: 0,
      }}
    >
      {plans.map((plan) => (
        <Grid
          key={plan.id}
          size={{
            xs: 12,
            sm: 6,
            lg: 4,
          }}
          sx={{
            display: "flex",
          }}
        >
          <PlanCard
            plan={plan}
            onSelect={onSelect}
          />
        </Grid>
      ))}
    </Grid>
  );
}