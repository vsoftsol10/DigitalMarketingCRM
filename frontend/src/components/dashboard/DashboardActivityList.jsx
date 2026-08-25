import { Stack } from "@mui/material";

import ActivityItem from "./ActivityItem";

export default function DashboardActivityList({
  activities = [],
  onActivityClick,
}) {
  return (
    <Stack spacing={1.2}>
      {activities.map((activity) => (
        <ActivityItem
          key={activity.id}
          activity={activity}
          onClick={onActivityClick}
        />
      ))}
    </Stack>
  );
}