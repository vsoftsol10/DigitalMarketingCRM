import { Stack } from "@mui/material";

import NotificationItem from "./NotificationItem";

export default function DashboardNotificationList({
  notifications = [],
  onNotificationClick,
}) {
  return (
    <Stack spacing={1.2}>
      {notifications.map((notification) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onClick={onNotificationClick}
        />
      ))}
    </Stack>
  );
}
