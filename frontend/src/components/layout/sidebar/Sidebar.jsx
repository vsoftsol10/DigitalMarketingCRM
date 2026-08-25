import { Drawer, Box, Divider } from "@mui/material";

import SidebarHeader from "./SidebarHeader";
import SidebarSection from "./SidebarSection";
import SidebarFooter from "./SidebarFooter";

import { navigation } from "../../../constants/navigation";

const drawerWidth = 280;

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
          borderRight: "1px solid #E5E7EB",
          bgcolor: "#FFFFFF",
        },
      }}
    >
      <SidebarHeader />

      <Divider />

      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
          p: 2,
        }}
      >
        {navigation.map((section) => (
          <SidebarSection
            key={section.title}
            title={section.title}
            items={section.items}
          />
        ))}
      </Box>

      <Divider />

      <SidebarFooter />
    </Drawer>
  );
}