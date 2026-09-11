import { Box, Button, CircularProgress, Typography } from "@mui/material";

import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import YouTubeIcon from "@mui/icons-material/YouTube";
import ApartmentRoundedIcon from "@mui/icons-material/ApartmentRounded";

// ============================================================
// PLATFORM ICONS
// ============================================================

const PLATFORM_ICONS = {
  meta: FacebookRoundedIcon,
  instagram: InstagramIcon,
  facebook: FacebookRoundedIcon,
  linkedin: LinkedInIcon,
  youtube: YouTubeIcon,
};

// ============================================================
// COMPONENT
// ============================================================

export default function ConnectSocialAccountCard({
  platform,

  name,
  backgroundColor,
  iconColor,

  connected = false,
  disabled = false,
  loading = false,

  onConnect,
}) {
  const platformId =
    typeof platform === "string" ? platform : platform?.id || "";

  const platformName =
    name ||
    (typeof platform === "object" ? platform?.name : "") ||
    platformId ||
    "Social account";

  const platformDescription =
    typeof platform === "object" ? platform?.description || "" : "";

  const platformBackgroundColor =
    backgroundColor ||
    (typeof platform === "object" ? platform?.backgroundColor : "") ||
    "#F1F5F9";

  const platformIconColor =
    iconColor ||
    (typeof platform === "object" ? platform?.iconColor : "") ||
    "#475569";

  const comingSoon =
    typeof platform === "object" && Boolean(platform?.comingSoon);

  const Icon = PLATFORM_ICONS[platformId] || ApartmentRoundedIcon;

  const handleConnect = () => {
    if (disabled || loading || typeof onConnect !== "function") {
      return;
    }

    onConnect(platform);
  };

  return (
    <Box
      sx={{
        flex: "1 1 180px",

        minWidth: {
          xs: 160,
          sm: 180,
        },

        maxWidth: 210,

        minHeight: 150,

        p: 2,

        borderRadius: "16px",

        border: "1px solid #E2E8F0",

        bgcolor: "#FFFFFF",

        display: "flex",

        flexDirection: "column",

        alignItems: "center",

        justifyContent: "center",

        textAlign: "center",

        transition:
          "border-color .2s ease, box-shadow .2s ease, transform .2s ease",

        opacity: disabled ? 0.55 : 1,

        "&:hover": disabled
          ? {}
          : {
              borderColor: "#2563EB",
              bgcolor: "#F8FBFF",
              transform: "translateY(-2px)",
              boxShadow: "0 8px 20px rgba(15,23,42,.06)",
            },
      }}
    >
      <Box
        sx={{
          width: 44,
          height: 44,
          borderRadius: "12px",
          bgcolor: platformBackgroundColor,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          mb: 1.25,
        }}
      >
        <Icon
          sx={{
            fontSize: 23,
            color: platformIconColor,
          }}
        />
      </Box>

      <Typography
        component="p"
        sx={{
          fontSize: 14,
          fontWeight: 600,
          color: "#334155",
          lineHeight: 1.4,
          mb: 0.35,
        }}
      >
        {platformName}
      </Typography>

      {platformDescription && (
        <Typography
          component="p"
          sx={{
            fontSize: 12,
            color: "#94A3B8",
            lineHeight: 1.4,
            mb: 1.25,
          }}
        >
          {platformDescription}
        </Typography>
      )}

      <Button
        type="button"
        variant="outlined"
        size="small"
        onClick={handleConnect}
        disabled={disabled || loading || typeof onConnect !== "function"}
        aria-label={
          comingSoon ? `${platformName} coming soon` : `Connect ${platformName}`
        }
        startIcon={
          loading ? <CircularProgress size={14} color="inherit" /> : null
        }
        sx={{
          minWidth: 105,
          height: 34,
          px: 1.5,
          borderRadius: "10px",
          borderColor: "#CBD5E1",
          color: "#475569",
          textTransform: "none",
          fontSize: 13,
          fontWeight: 600,
          boxShadow: "none",

          "&:hover": {
            borderColor: "#2563EB",
            color: "#2563EB",
            bgcolor: "#F8FBFF",
            boxShadow: "none",
          },

          "&.Mui-disabled": {
            borderColor: "#E2E8F0",
            color: "#94A3B8",
            bgcolor: "transparent",
          },
        }}
      >
        {loading ? "Connecting..." : comingSoon ? "Coming soon" : "Connect"}
      </Button>
    </Box>
  );
}
