import { Box, Typography } from "@mui/material";

import SidebarItem from "./SidebarItem";

export default function SidebarSection({
  title,
  items,
}) {
  return (
    <Box
      sx={{
        mb: 1.1,
        "@media (max-height: 700px)": { mb: 0.6 },
        "@media (max-height: 600px)": { mb: 0.35 },
        "@media (max-height: 520px)": { mb: 0 },
      }}
    >
      <Typography
        sx={{
          px: 2,
          mb: 0.5,
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: 0.7,
          color: "#8290AD",
          "@media (max-height: 700px)": { mb: 0.3 },
          "@media (max-height: 600px)": { mb: 0.2 },
          "@media (max-height: 520px)": { mb: 0 },
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
