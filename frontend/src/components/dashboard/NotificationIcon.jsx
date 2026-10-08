import { Box } from "@mui/material";

import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";
import NotificationsActiveOutlinedIcon from "@mui/icons-material/NotificationsActiveOutlined";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import CheckCircleOutlineRoundedIcon from "@mui/icons-material/CheckCircleOutlineRounded";

const CONFIG = {
  FAILED_POST: {
    icon: WarningAmberRoundedIcon,
    color: "#EF4444",
    background: "#FEF2F2",
  },

  SUBSCRIPTION_EXPIRING: {
    icon: NotificationsActiveOutlinedIcon,
    color: "#F59E0B",
    background: "#FFFBEB",
  },

  SUBSCRIPTION_EXPIRED: {
    icon: WarningAmberRoundedIcon,
    color: "#EF4444",
    background: "#FEF2F2",
  },

  POST_PUBLISHED: {
    icon: CheckCircleOutlineRoundedIcon,
    color: "#16A34A",
    background: "#F0FDF4",
  },

  SUBSCRIPTION_ACTIVATED: {
    icon: CheckCircleOutlineRoundedIcon,
    color: "#16A34A",
    background: "#F0FDF4",
  },

  DEFAULT: {
    icon: InfoOutlinedIcon,
    color: "#64748B",
    background: "#F8FAFC",
  },
};

export default function NotificationIcon({ type }) {
  const config = CONFIG[type] || CONFIG.DEFAULT;

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
