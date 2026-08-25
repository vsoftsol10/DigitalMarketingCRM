import { Box, Typography } from "@mui/material";

import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import YouTubeIcon from "@mui/icons-material/YouTube";
import XIcon from "@mui/icons-material/X";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";

const iconMap = {
  INSTAGRAM: InstagramIcon,
  FACEBOOK: FacebookRoundedIcon,
  LINKEDIN: LinkedInIcon,
  YOUTUBE: YouTubeIcon,
  THREADS: SmartToyOutlinedIcon,
  X: XIcon,
};

export default function PreviewPlatformChip({
  platform,
  selected,
  onClick,
}) {
  const Icon = iconMap[platform];

  return (
    <Box
      onClick={onClick}
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1,

        px: 2,
        py: 1,

        borderRadius: "999px",

        cursor: "pointer",

        border: selected
          ? "1px solid #2563EB"
          : "1px solid #E2E8F0",

        bgcolor: selected
          ? "#EFF6FF"
          : "#FFFFFF",

        transition: ".2s",

        "&:hover": {
          borderColor: "#2563EB",
          bgcolor: "#F8FAFC",
        },
      }}
    >
      {Icon && (
        <Icon
          sx={{
            fontSize: 18,
            color: selected
              ? "#2563EB"
              : "#64748B",
          }}
        />
      )}

      <Typography
        sx={{
          fontSize: 13,
          fontWeight: 600,
          color: selected
            ? "#2563EB"
            : "#475569",
        }}
      >
        {platform}
      </Typography>
    </Box>
  );
}