import { Stack } from "@mui/material";

import QuickActionItem from "./QuickActionItem";

export default function DashboardQuickActionList({
  actions = [],
  onActionClick,
}) {
  return (
    <Stack spacing={2}>
      {actions.map((action) => (
        <QuickActionItem
          key={action.id}
          action={action}
          onClick={onActionClick}
        />
      ))}
    </Stack>
  );
}