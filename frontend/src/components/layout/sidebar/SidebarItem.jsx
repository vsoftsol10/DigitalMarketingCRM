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
        height: 42,
        minHeight: 42,
        borderRadius: "16px",
        px: 1.75,
        py: 0.75,
        mb: 0.25,
        position: "relative",

        background: active ? "#FFFFFF" : "transparent",
        border: active ? "1px solid #E6E8F2" : "1px solid transparent",
        boxShadow: active ? "0 3px 8px rgba(52,64,112,.06)" : "none",

        color: active ? "#7042E8" : "#53627F",

        "@media (max-height: 700px)": {
          height: 36,
          minHeight: 36,
          py: 0.5,
          mb: 0.15,
        },

        "@media (max-height: 600px)": {
          height: 32,
          minHeight: 32,
          py: 0.25,
          mb: 0.05,
        },

        "@media (max-height: 520px)": {
          mb: 0,
        },

        "@media (max-height: 460px)": {
          height: 28,
          minHeight: 28,
          py: 0,
        },

        "&:hover": {
          bgcolor: "rgba(237, 241, 255, .7)",
        },
      }}
    >
      <ListItemIcon
        sx={{
          color: active ? "#7042E8" : "#8290A8",
          minWidth: 36,
        }}
      >
        <Icon sx={{ fontSize: 20 }} />
      </ListItemIcon>

      <ListItemText
        primary={label}
        primaryTypographyProps={{
          fontSize: 14,
          fontWeight: active ? 650 : 500,
        }}
      />

      {active && (
        <Box
          sx={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            bgcolor: "#7042E8",
            boxShadow: "0 0 0 3px rgba(112,66,232,.1)",
          }}
        />
      )}
    </ListItemButton>
  );
}
