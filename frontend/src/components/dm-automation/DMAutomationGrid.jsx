import { Box } from "@mui/material";

import DMAutomationCard from "./DMAutomationCard";

export default function DMAutomationGrid({
  automations,
  onEdit,
  onToggleStatus,
}) {
  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: {
          xs: "1fr",
          md: "repeat(2, minmax(0, 1fr))",
          xl: "repeat(3, minmax(0, 1fr))",
        },
        gap: 2.5,
        width: "100%",
      }}
    >
      {automations.map((automation) => (
        <DMAutomationCard
          key={automation.id}
          automation={automation}
          onEdit={onEdit}
          onToggleStatus={onToggleStatus}
        />
      ))}
    </Box>
  );
}