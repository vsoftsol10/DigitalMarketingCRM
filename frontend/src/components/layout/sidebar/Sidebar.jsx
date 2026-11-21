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
          top: 0,
          left: 0,
          height: "100%",
          border: "none",
          borderRight: "1px solid #DDE3F1",
          borderRadius: 0,
          background: "rgba(248,250,255,.94)",
          backdropFilter: "blur(22px)",
          boxShadow: "none",
        },
      }}
    >
      <SidebarHeader />

      <Divider sx={{ borderColor: "#DDE3F1" }} />

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
