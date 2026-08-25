import { Box, Typography } from "@mui/material";

import SidebarItem from "./SidebarItem";

export default function SidebarSection({
  title,
  items,
}) {
  return (
    <Box sx={{ mb: 3 }}>
      <Typography
        sx={{
          px: 2,
          mb: 1,
          fontSize: 12,
          fontWeight: 700,
          letterSpacing: 1,
          color: "#94A3B8",
        }}
      >
        {title}
      </Typography>

      {items.map((item) => (
        <SidebarItem
          key={item.path}
          {...item}
        />
      ))}
    </Box>
  );
}