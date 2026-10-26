import { Box } from "@mui/material";

import CheckCircleOutlineRoundedIcon from "@mui/icons-material/CheckCircleOutlineRounded";
import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import ErrorOutlineRoundedIcon from "@mui/icons-material/ErrorOutlineRounded";
import AutorenewRoundedIcon from "@mui/icons-material/AutorenewRounded";
import CancelOutlinedIcon from "@mui/icons-material/CancelOutlined";
import WorkspacePremiumOutlinedIcon from "@mui/icons-material/WorkspacePremiumOutlined";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

const CONFIG = {
  POST_PUBLISHED: {
    icon: CheckCircleOutlineRoundedIcon,
    color: "#10B981",
    background: "#E7F8F1",
  },

  ORGANIZATION_CREATED: {
    icon: BusinessOutlinedIcon,
    color: "#2563EB",
    background: "#E8F1FF",
  },

  SUBSCRIPTION_ACTIVATED: {
    icon: WorkspacePremiumOutlinedIcon,
    color: "#2563EB",
    background: "#EDE8FF",
  },

  SUBSCRIPTION_RENEWED: {
    icon: AutorenewRoundedIcon,
    color: "#2563EB",
    background: "#E8EEFF",
  },

  SUBSCRIPTION_CANCELLED: {
    icon: CancelOutlinedIcon,
    color: "#64748B",
    background: "#F0EBFF",
  },

  POST_CREATED: {
    icon: AddCircleOutlineRoundedIcon,
    color: "#F97316",
    background: "#EEF1F8",
  },

  POST_SCHEDULED: {
    icon: ScheduleOutlinedIcon,
    color: "#2563EB",
    background: "#E9F2FF",
  },

  POST_FAILED: {
    icon: ErrorOutlineRoundedIcon,
    color: "#EF4444",
    background: "#FFEAF0",
  },

  DEFAULT: {
    icon: InfoOutlinedIcon,
    color: "#64748B",
    background: "#EEF1F8",
  },
};

export default function ActivityIcon({ type }) {
  const config = CONFIG[type] || CONFIG.DEFAULT;

  const Icon = config.icon;

  return (
    <Box
      sx={{
        width: 40,
        height: 40,

        borderRadius: "12px",

        background: `linear-gradient(145deg, ${config.background}, rgba(255,255,255,.74))`,
        border: "1px solid rgba(255,255,255,.9)",
        boxShadow: "0 4px 9px rgba(76,98,154,.1), inset 0 1px 2px rgba(255,255,255,.92), inset 0 -1px 2px rgba(95,116,170,.08)",

        display: "flex",
        justifyContent: "center",
        alignItems: "center",

        flexShrink: 0,
      }}
    >
      <Icon
        sx={{
          fontSize: 20,
          color: config.color,
        }}
      />
    </Box>
  );
}
