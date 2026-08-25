import { Grid } from "@mui/material";

import LightbulbOutlinedIcon from "@mui/icons-material/LightbulbOutlined";
import CalendarMonthOutlinedIcon from "@mui/icons-material/CalendarMonthOutlined";
import CheckCircleOutlineRoundedIcon from "@mui/icons-material/CheckCircleOutlineRounded";
import RadioButtonUncheckedRoundedIcon from "@mui/icons-material/RadioButtonUncheckedRounded";

import ContentPlannerStatCard from "./ContentPlannerStatCard";

export default function ContentPlannerStats({ statistics = {} }) {
  const items = [
    {
      label: "Total Ideas",
      value: statistics.total_ideas ?? 0,
      icon: LightbulbOutlinedIcon,
    },
    {
      label: "Planned This Month",
      value: statistics.planned_this_month ?? 0,
      icon: CalendarMonthOutlinedIcon,
    },
    {
      label: "Using Content Planner",
      value: statistics.using_content_planner ?? 0,
      icon: CheckCircleOutlineRoundedIcon,
    },
    {
      label: "Not Using Content Planner",
      value: statistics.not_using_content_planner ?? 0,
      icon: RadioButtonUncheckedRoundedIcon,
    },
  ];

  return (
    <Grid container spacing={3}>
      {items.map((item) => (
        <Grid
          key={item.label}
          size={{
            xs: 12,
            sm: 6,
            lg: 3,
          }}
        >
          <ContentPlannerStatCard {...item} />
        </Grid>
      ))}
    </Grid>
  );
}