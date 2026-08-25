import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import InstagramIcon from "@mui/icons-material/Instagram";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import YouTubeIcon from "@mui/icons-material/YouTube";
import PinterestIcon from "@mui/icons-material/Pinterest";
import WhatsAppIcon from "@mui/icons-material/WhatsApp";
import TelegramIcon from "@mui/icons-material/Telegram";
import RedditIcon from "@mui/icons-material/Reddit";
import PublicRoundedIcon from "@mui/icons-material/PublicRounded";

import { XIcon, TikTokIcon } from "./BrandIcons";

// Single source of truth for platform → icon / brand color.
// Used by both the header badge and the Overview card so the
// same platform always renders identically across the panel.

const PLATFORM_META = {
  FACEBOOK: {
    label: "Facebook",
    icon: FacebookRoundedIcon,
    color: "#1877F2",
  },
  INSTAGRAM: {
    label: "Instagram",
    icon: InstagramIcon,
    color: "#E1306C",
  },
  TWITTER: {
    label: "X",
    icon: XIcon,
    color: "#0F1419",
  },
  X: {
    label: "X",
    icon: XIcon,
    color: "#0F1419",
  },
  LINKEDIN: {
    label: "LinkedIn",
    icon: LinkedInIcon,
    color: "#0A66C2",
  },
  YOUTUBE: {
    label: "YouTube",
    icon: YouTubeIcon,
    color: "#FF0000",
  },
  TIKTOK: {
    label: "TikTok",
    icon: TikTokIcon,
    color: "#000000",
  },
  PINTEREST: {
    label: "Pinterest",
    icon: PinterestIcon,
    color: "#E60023",
  },
  WHATSAPP: {
    label: "WhatsApp",
    icon: WhatsAppIcon,
    color: "#25D366",
  },
  TELEGRAM: {
    label: "Telegram",
    icon: TelegramIcon,
    color: "#26A5E4",
  },
  REDDIT: {
    label: "Reddit",
    icon: RedditIcon,
    color: "#FF4500",
  },
};

export function getPlatformMeta(platform) {
  if (!platform) {
    return null;
  }

  const key = platform.toString().trim().toUpperCase();

  return (
    PLATFORM_META[key] || {
      label: platform,
      icon: PublicRoundedIcon,
      color: null,
    }
  );
}