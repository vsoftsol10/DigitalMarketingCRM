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
        bgcolor: "#F8FAFC",
      }}
    >
      <Sidebar />

      <Box
        sx={{
          flex: 1,
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
            px: 5,
            py: 4,
            overflowY: "auto",
          }}
        >
          <Box
            sx={{
              width: "100%",
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
