import { ListItemButton, ListItemIcon, ListItemText, Box } from "@mui/material";

import { NavLink, useLocation } from "react-router-dom";

export default function SidebarItem({ label, path, icon: Icon }) {
  const location = useLocation();

  const active =
    location.pathname === path || location.pathname.startsWith(path + "/");

  return (
    <ListItemButton
      component={NavLink}
      to={path}
      sx={{
        height: 44,
        borderRadius: 12,
        px: 2,
        mb: 0.5,

        bgcolor: active ? "#EEF4FF" : "transparent",

        color: active ? "#2563EB" : "#334155",

        "&:hover": {
          bgcolor: "#F8FAFC",
        },
      }}
    >
      <ListItemIcon
        sx={{
          color: "inherit",
          minWidth: 34,
        }}
      >
        <Icon sx={{ fontSize: 20 }} />
      </ListItemIcon>

      <ListItemText
        primary={label}
        primaryTypographyProps={{
          fontSize: 14,
          fontWeight: active ? 600 : 500,
        }}
      />

      {active && (
        <Box
          sx={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            bgcolor: "#2563EB",
          }}
        />
      )}
    </ListItemButton>
  );
}
