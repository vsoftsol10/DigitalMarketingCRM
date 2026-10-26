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

export default function NotificationIcon({ type, raised = false }) {
  const config = CONFIG[type] || CONFIG.DEFAULT;

  const Icon = config.icon;

  return (
    <Box
      sx={{
        width: 44,
        height: 44,

        borderRadius: "12px",

        background: raised
          ? `linear-gradient(145deg, ${config.background}, rgba(255,255,255,.78))`
          : config.background,
        border: raised ? "1px solid rgba(255,255,255,.92)" : "none",
        boxShadow: raised
          ? "0 4px 9px rgba(76,98,154,.1), inset 0 1px 2px rgba(255,255,255,.92), inset 0 -1px 2px rgba(95,116,170,.08)"
          : "none",

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
