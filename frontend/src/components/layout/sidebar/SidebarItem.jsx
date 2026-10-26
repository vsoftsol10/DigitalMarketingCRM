import { ListItemButton, ListItemIcon, ListItemText, Box } from "@mui/material";

import { NavLink, useLocation } from "react-router-dom";

const ICON_COLORS = {
  "/": "#5B5DD4",
  "/organizations": "#3F70B8",
  "/planner": "#7951D2",
  "/posts": "#287FCF",
  "/calendar": "#168DB8",
  "/dm-automation": "#8756D7",
  "/ads": "#B84FC7",
  "/insights": "#3E78C5",
  "/plans": "#7586A5",
  "/settings": "#7586A5",
};

export default function SidebarItem({ label, path, icon: Icon }) {
  const location = useLocation();
  const iconColor = ICON_COLORS[path] || "#8292B1";

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

        background: active
          ? "linear-gradient(110deg, rgba(232,235,255,.98), rgba(239,244,255,.94))"
          : "transparent",
        border: active ? "1px solid rgba(119, 135, 230, .24)" : "1px solid transparent",
        boxShadow: active
          ? "0 7px 15px rgba(78, 103, 186, .16), 0 2px 4px rgba(83, 104, 177, .08), inset 0 2px 3px rgba(255,255,255,.95), inset 0 -1px 2px rgba(106,125,199,.08)"
          : "none",

        color: active ? "#3D66D8" : "#53627F",

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
          bgcolor: "rgba(238, 243, 255, .74)",
        },
      }}
    >
      <ListItemIcon
        sx={{
          color: iconColor,
          minWidth: 36,
        }}
      >
        <Icon sx={{ fontSize: 20, filter: "drop-shadow(0 1px 1px rgba(44,63,111,.18))" }} />
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
            bgcolor: "#4B74E8",
            boxShadow: "0 0 0 3px rgba(75,116,232,.12)",
          }}
        />
      )}
    </ListItemButton>
  );
}
