import { Drawer, Box, Divider } from "@mui/material";

import SidebarHeader from "./SidebarHeader";
import SidebarSection from "./SidebarSection";

import { navigation } from "../../../constants/navigation";

const drawerWidth = 296;

export default function Sidebar() {
  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,

        "& .MuiDrawer-paper": {
          width: drawerWidth,
          display: "flex",
          flexDirection: "column",
          boxSizing: "border-box",
          overflow: "hidden",
          top: 8,
          left: 8,
          height: "calc(100% - 16px)",
          border: "1px solid rgba(255, 255, 255, 0.9)",
          borderRadius: "26px",
          background: "linear-gradient(155deg, rgba(247,250,255,.97) 0%, rgba(239,245,255,.94) 55%, rgba(235,242,255,.92) 100%)",
          backdropFilter: "blur(22px)",
          boxShadow: "0 18px 40px rgba(76,98,156,.16), 0 3px 10px rgba(80,101,157,.07), inset 0 1px 0 rgba(255,255,255,.98), inset 0 -1px 3px rgba(113,137,190,.12)",
        },
      }}
    >
      <SidebarHeader />

      <Divider sx={{ borderColor: "rgba(148, 163, 184, 0.16)" }} />

      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          overflowY: "hidden",
          px: 1.75,
          py: 2,
          "@media (max-height: 700px)": {
            py: 0.5,
          },
          "@media (max-height: 600px)": {
            py: 0.25,
          },
          "@media (max-height: 520px)": {
            py: 0,
          },
        }}
      >
        {navigation.map((section) => (
          <Box key={section.title}>
            {section.title === "SYSTEM" && (
              <Divider
                sx={{
                  my: 1.2,
                  borderColor: "rgba(148, 163, 184, 0.24)",
                  "@media (max-height: 700px)": { my: 0.7 },
                  "@media (max-height: 600px)": { my: 0.4 },
                  "@media (max-height: 520px)": { my: 0.1 },
                }}
              />
            )}
            <SidebarSection
              title={section.title}
              items={section.items}
            />
          </Box>
        ))}
      </Box>

    </Drawer>
  );
}
