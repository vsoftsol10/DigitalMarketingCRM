import { Grid } from "@mui/material";

import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";
import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";
import CampaignOutlinedIcon from "@mui/icons-material/CampaignOutlined";

import DashboardStatCard from "./DashboardStatCard";

export default function DashboardStats({ statistics }) {
  const items = [
    {
      label: "Total Organizations",
      value: statistics?.total_organizations ?? 0,
      icon: BusinessOutlinedIcon,
    },
    {
      label: "Connected Social Accounts",
      value: statistics?.connected_social_accounts ?? 0,
      icon: ShareOutlinedIcon,
    },
    {
      label: "Scheduled Posts Today",
      value: statistics?.scheduled_posts_today ?? 0,
      icon: CalendarTodayOutlinedIcon,
    },
    {
      label: "Active Campaigns",
      value: statistics?.active_campaigns ?? 0,
      icon: CampaignOutlinedIcon,
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
          <DashboardStatCard {...item} />
        </Grid>
      ))}
    </Grid>
  );
}