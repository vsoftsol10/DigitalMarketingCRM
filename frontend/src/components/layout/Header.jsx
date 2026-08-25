import {
  AppBar,
  Toolbar,
  Box,
  Typography,
  Avatar,
  IconButton,
  TextField,
  InputAdornment,
  Badge,
} from "@mui/material";

import HomeOutlinedIcon from "@mui/icons-material/HomeOutlined";
import SearchIcon from "@mui/icons-material/Search";
import NotificationsNoneOutlinedIcon from "@mui/icons-material/NotificationsNoneOutlined";

export default function Header() {
  return (
    <AppBar
      position="sticky"
      elevation={0}
      color="inherit"
      sx={{
        bgcolor: "#FFFFFF",
        borderBottom: "1px solid #E5E7EB",
      }}
    >
      <Toolbar
        sx={{
          height: 80,
          px: "32px !important",
          display: "flex",
          justifyContent: "space-between",
        }}
      >
        {/* Left */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
          }}
        >
          <HomeOutlinedIcon
            sx={{
              fontSize: 20,
              color: "#64748B",
            }}
          />

          <Typography
            sx={{
              fontSize: 16,
              fontWeight: 600,
              color: "#1E293B",
            }}
          >
            Dashboard
          </Typography>
        </Box>

        {/* Right */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2.5,
          }}
        >
          <TextField
            size="small"
            placeholder="Search..."
            sx={{
              width: 400,

              "& .MuiOutlinedInput-root": {
                height: 46,
                borderRadius: "18px",
                bgcolor: "#F8FAFC",

                "& fieldset": {
                  border: "none",
                },

                "&:hover fieldset": {
                  border: "none",
                },

                "&.Mui-focused fieldset": {
                  border: "1px solid #2563EB",
                },
              },

              "& input": {
                fontSize: 15,
              },
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon
                    sx={{
                      color: "#94A3B8",
                    }}
                  />
                </InputAdornment>
              ),
            }}
          />

          <IconButton>
            <Badge
              color="error"
              variant="dot"
              overlap="circular"
            >
              <NotificationsNoneOutlinedIcon
                sx={{
                  fontSize: 24,
                  color: "#475569",
                }}
              />
            </Badge>
          </IconButton>

          <Avatar
            sx={{
              width: 44,
              height: 44,
              bgcolor: "#2563EB",
              fontSize: 16,
              fontWeight: 700,
            }}
          >
            AR
          </Avatar>
        </Box>
      </Toolbar>
    </AppBar>
  );
}