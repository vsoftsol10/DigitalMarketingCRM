import { Outlet } from "react-router-dom";
import { Box } from "@mui/material";

import Sidebar from "../components/layout/sidebar/Sidebar";
import Header from "../components/layout/Header";

export default function DashboardLayout() {
  return (
    <Box
      sx={{
        display: "flex",
        minHeight: "100vh",
        bgcolor: "#F2F5FF",
        backgroundImage: "linear-gradient(135deg, #F7F9FF 0%, #F1F5FF 58%, #F7F2FF 100%)",
      }}
    >
      <Sidebar />

      <Box
        sx={{
          flex: 1,
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Header />

        {/* <Box
          component="main"
          sx={{
            flex: 1,
            p: 3,
          }}
        >
          <Outlet />
        </Box> */}
        <Box
          component="main"
          sx={{
            flex: 1,
            minWidth: 0,
            px: 5,
            py: 4,
            overflowY: "auto",
          }}
        >
          <Box
            sx={{
              width: "100%",
              minWidth: 0,
              // maxWidth: "1320px",
              maxWidth: "1180px",
              mx: "auto",
            }}
          >
            <Outlet />
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
