import { Box } from "@mui/material";

import AddPhotoAlternateOutlinedIcon from "@mui/icons-material/AddPhotoAlternateOutlined";
import EventNoteOutlinedIcon from "@mui/icons-material/EventNoteOutlined";
import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";
import BoltOutlinedIcon from "@mui/icons-material/BoltOutlined";

const CONFIG = {
  post: {
    icon: AddPhotoAlternateOutlinedIcon,
    color: "#287FCF",
    background: "#E5F0FF",
  },

  planner: {
    icon: EventNoteOutlinedIcon,
    color: "#7652D2",
    background: "#EEE8FF",
  },

  organization: {
    icon: BusinessOutlinedIcon,
    color: "#3F70B8",
    background: "#E5EEFF",
  },

  calendar: {
    icon: CalendarTodayOutlinedIcon,
    color: "#168DB8",
    background: "#DFF4FB",
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

        background: `linear-gradient(145deg, ${config.background}, rgba(255,255,255,.76))`,
        border: "1px solid rgba(255,255,255,.92)",
        boxShadow: "0 5px 10px rgba(76,98,154,.12), inset 0 2px 2px rgba(255,255,255,.96), inset 0 -1px 2px rgba(93,112,162,.08)",

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
