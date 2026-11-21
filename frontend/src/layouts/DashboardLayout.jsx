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
        bgcolor: "#EDF1FF",
        backgroundImage: "linear-gradient(110deg, #EDF1FF 0%, #F1EDFF 55%, #EFE8FF 100%)",
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
