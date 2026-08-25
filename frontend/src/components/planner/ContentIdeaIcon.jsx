import { Avatar } from "@mui/material";

import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookIcon from "@mui/icons-material/Facebook";
import YouTubeIcon from "@mui/icons-material/YouTube";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import XIcon from "@mui/icons-material/X";

const PLATFORM_CONFIG = {
  INSTAGRAM: {
    icon: InstagramIcon,
    color: "#E1306C",
    background: "#FCE7F3",
  },

  FACEBOOK: {
    icon: FacebookIcon,
    color: "#1877F2",
    background: "#EFF6FF",
  },

  YOUTUBE: {
    icon: YouTubeIcon,
    color: "#FF0000",
    background: "#FEF2F2",
  },

  LINKEDIN: {
    icon: LinkedInIcon,
    color: "#0A66C2",
    background: "#EFF6FF",
  },

  X: {
    icon: XIcon,
    color: "#111827",
    background: "#F8FAFC",
  },
};

export default function ContentIdeaIcon({ platform }) {
  const config = PLATFORM_CONFIG[platform] || PLATFORM_CONFIG.INSTAGRAM;

  const Icon = config.icon;

  return (
    <Avatar
      sx={{
        width: 44,
        height: 44,

        bgcolor: config.background,
      }}
    >
      <Icon
        sx={{
          color: config.color,
          fontSize: 22,
        }}
      />
    </Avatar>
  );
}
