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
    background: "#F8FAFC",
  },

  ORGANIZATION_CREATED: {
    icon: BusinessOutlinedIcon,
    color: "#2563EB",
    background: "#F8FAFC",
  },

  SUBSCRIPTION_ACTIVATED: {
    icon: WorkspacePremiumOutlinedIcon,
    color: "#2563EB",
    background: "#F8FAFC",
  },

  SUBSCRIPTION_RENEWED: {
    icon: AutorenewRoundedIcon,
    color: "#2563EB",
    background: "#F8FAFC",
  },

  SUBSCRIPTION_CANCELLED: {
    icon: CancelOutlinedIcon,
    color: "#64748B",
    background: "#F8FAFC",
  },

  POST_CREATED: {
    icon: AddCircleOutlineRoundedIcon,
    color: "#F97316",
    background: "#F8FAFC",
  },

  POST_SCHEDULED: {
    icon: ScheduleOutlinedIcon,
    color: "#2563EB",
    background: "#F8FAFC",
  },

  POST_FAILED: {
    icon: ErrorOutlineRoundedIcon,
    color: "#EF4444",
    background: "#F8FAFC",
  },

  DEFAULT: {
    icon: InfoOutlinedIcon,
    color: "#64748B",
    background: "#F8FAFC",
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

        bgcolor: config.background,

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
