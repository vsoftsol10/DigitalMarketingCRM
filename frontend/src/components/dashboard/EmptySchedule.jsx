import { Box, Button, Typography } from "@mui/material";

import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";
import AddRoundedIcon from "@mui/icons-material/AddRounded";

export default function EmptySchedule({
  onCreatePost,
}) {
  return (
    <Box
      sx={{
        minHeight: 360,

        display: "flex",
        flexDirection: "column",

        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <Box
        sx={{
          width: 58,
          height: 58,

          borderRadius: "50%",

          bgcolor: "#F1F5F9",

          display: "flex",
          justifyContent: "center",
          alignItems: "center",

          mb: 3,
        }}
      >
        <CalendarTodayOutlinedIcon
          sx={{
            color: "#64748B",
          }}
        />
      </Box>

      <Typography
        sx={{
          fontSize: 30,
          fontWeight: 700,
          color: "#1E293B",
        }}
      >
        Nothing scheduled today
      </Typography>

      <Typography
        sx={{
          mt: 1,
          maxWidth: 420,

          textAlign: "center",

          fontSize: 16,
          color: "#64748B",
          lineHeight: 1.7,
        }}
      >
        Your calendar is clear. Create a post to fill today's schedule.
      </Typography>

      <Button
        variant="contained"
        startIcon={<AddRoundedIcon />}
        onClick={onCreatePost}
        sx={{
          mt: 4,

          height: 46,

          px: 3,

          borderRadius: "14px",

          textTransform: "none",

          fontWeight: 600,

          boxShadow: "none",

          "&:hover": {
            boxShadow: "none",
          },
        }}
      >
        Create Post
      </Button>
    </Box>
  );
}