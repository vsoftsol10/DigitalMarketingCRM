import {
  Box,
  Checkbox,
  Stack,
  Typography,
} from "@mui/material";

import CheckRoundedIcon from "@mui/icons-material/CheckRounded";

import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import YouTubeIcon from "@mui/icons-material/YouTube";
import XIcon from "@mui/icons-material/X";
import ForumRoundedIcon from "@mui/icons-material/ForumRounded";

import { TYPOGRAPHY } from "../../../theme/typography";

const PLATFORM_CONFIG = {
  instagram: {
    icon: InstagramIcon,
    bg: "#FCE7F3",
    color: "#E1306C",
  },

  facebook: {
    icon: FacebookRoundedIcon,
    bg: "#EFF6FF",
    color: "#1877F2",
  },

  linkedin: {
    icon: LinkedInIcon,
    bg: "#EFF6FF",
    color: "#0A66C2",
  },

  youtube: {
    icon: YouTubeIcon,
    bg: "#FEF2F2",
    color: "#FF0000",
  },

  threads: {
    icon: ForumRoundedIcon,
    bg: "#F8FAFC",
    color: "#111827",
  },

  x: {
    icon: XIcon,
    bg: "#F8FAFC",
    color: "#111827",
  },
};

export default function PlatformCard({
  platform,
  selected,
  onClick,
}) {
  const config =
    PLATFORM_CONFIG[
      platform.icon?.toLowerCase()
    ];

  const Icon = config?.icon;

  const disabled = !platform.connected;

  return (
    <Box
      onClick={disabled ? undefined : onClick}
      sx={{
        p: 2.25,

        borderRadius: "18px",

        border: selected
          ? "2px solid #2563EB"
          : "1px solid #E2E8F0",

        bgcolor: selected
          ? "#F8FBFF"
          : "#FFFFFF",

        cursor: disabled
          ? "not-allowed"
          : "pointer",

        opacity: disabled ? 0.55 : 1,

        transition: ".25s",

        "&:hover": disabled
          ? {}
          : {
              borderColor: "#2563EB",
              bgcolor: "#F8FBFF",
            },
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        spacing={2}
      >
        {/* Icon */}

        <Box
          sx={{
            width: 52,
            height: 52,

            borderRadius: "14px",

            bgcolor: config.bg,

            display: "flex",

            alignItems: "center",

            justifyContent: "center",

            flexShrink: 0,
          }}
        >
          {Icon && (
            <Icon
              sx={{
                fontSize: 24,
                color: config.color,
              }}
            />
          )}
        </Box>

        {/* Content */}

        <Box
          sx={{
            flex: 1,
            minWidth: 0,
          }}
        >
          <Typography
            sx={{
              ...TYPOGRAPHY.cardTitle,

              fontSize: 15,
            }}
          >
            {platform.name}
          </Typography>

          <Typography
            sx={{
              ...TYPOGRAPHY.bodySmall,

              color: platform.connected
                ? "#64748B"
                : "#EF4444",

              mt: .4,
            }}
          >
            {platform.connected
              ? "Connected"
              : "Not Connected"}
          </Typography>
        </Box>

        {/* Checkbox */}

        <Checkbox
          checked={selected}
          disabled={disabled}
          checkedIcon={
            <CheckRoundedIcon />
          }
          sx={{
            p: 0,

            color: "#CBD5E1",

            "&.Mui-checked": {
              color: "#2563EB",
            },
          }}
        />
      </Stack>
    </Box>
  );
}