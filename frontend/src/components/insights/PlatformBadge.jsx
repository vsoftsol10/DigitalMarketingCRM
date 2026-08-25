import { Chip } from "@mui/material";

const PLATFORM_CONFIG = {
  INSTAGRAM: {
    label: "Instagram",
    background: "#FDF2F8",
    color: "#DB2777",
  },

  FACEBOOK: {
    label: "Facebook",
    background: "#EFF6FF",
    color: "#2563EB",
  },

  LINKEDIN: {
    label: "LinkedIn",
    background: "#EFF6FF",
    color: "#0284C7",
  },

  YOUTUBE: {
    label: "YouTube",
    background: "#FEF2F2",
    color: "#DC2626",
  },

  X: {
    label: "X",
    background: "#F8FAFC",
    color: "#334155",
  },

  DEFAULT: {
    label: "Unknown",
    background: "#F8FAFC",
    color: "#64748B",
  },
};

export default function PlatformBadge({
  platform,
}) {
  const config =
    PLATFORM_CONFIG[platform] ||
    PLATFORM_CONFIG.DEFAULT;

  return (
    <Chip
      label={config.label}
      size="small"
      sx={{
        height: 28,

        borderRadius: "999px",

        bgcolor: config.background,

        color: config.color,

        fontSize: 13,
        fontWeight: 600,

        "& .MuiChip-label": {
          px: 1.5,
        },
      }}
    />
  );
}