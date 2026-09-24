import { Box } from "@mui/material";

import AddPhotoAlternateOutlinedIcon from "@mui/icons-material/AddPhotoAlternateOutlined";
import EventNoteOutlinedIcon from "@mui/icons-material/EventNoteOutlined";
import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";
import BoltOutlinedIcon from "@mui/icons-material/BoltOutlined";

const CONFIG = {
  post: {
    icon: AddPhotoAlternateOutlinedIcon,
    color: "#2563EB",
    background: "#EEF4FF",
  },

  planner: {
    icon: EventNoteOutlinedIcon,
    color: "#16A34A",
    background: "#ECFDF3",
  },

  organization: {
    icon: BusinessOutlinedIcon,
    color: "#7C3AED",
    background: "#F3E8FF",
  },

  calendar: {
    icon: CalendarTodayOutlinedIcon,
    color: "#D97706",
    background: "#FFF7ED",
  },

  default: {
    icon: BoltOutlinedIcon,
    color: "#64748B",
    background: "#F8FAFC",
  },
};

export default function QuickActionIcon({
  icon,
}) {
  const config =
    CONFIG[icon] || CONFIG.default;

  const Icon = config.icon;

  return (
    <Box
      sx={{
        width: 44,
        height: 44,

        borderRadius: "12px",

        bgcolor: config.background,

        display: "flex",
        justifyContent: "center",
        alignItems: "center",

        flexShrink: 0,
      }}
    >
      <Icon
        sx={{
          fontSize: 22,
          color: config.color,
        }}
      />
    </Box>
  );
}
