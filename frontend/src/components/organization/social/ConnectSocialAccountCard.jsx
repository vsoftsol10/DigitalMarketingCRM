import { Box, Button, Typography } from "@mui/material";

import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import YouTubeIcon from "@mui/icons-material/YouTube";
import ApartmentRoundedIcon from "@mui/icons-material/ApartmentRounded";
import overviewGlassCardSx from "../overview/overviewGlassCardSx";

// ============================================================
// PLATFORM ICONS
// ============================================================

const PLATFORM_ICONS = {
  facebook: FacebookRoundedIcon,
  instagram: InstagramIcon,
  linkedin: LinkedInIcon,
  youtube: YouTubeIcon,

  // Backward compatibility for any legacy component/config.
  meta: FacebookRoundedIcon,
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
  overviewStyle = false,

  onConnect,
}) {
  // ==========================================================
  // PLATFORM ID
  // ==========================================================

  const platformId =
    typeof platform === "string" ? platform : platform?.id || "";

  // ==========================================================
  // PLATFORM NAME
  // ==========================================================

  const platformName =
    name ||
    (typeof platform === "object" ? platform?.name : "") ||
    platformId ||
    "Social account";

  // ==========================================================
  // PLATFORM DESCRIPTION
  // ==========================================================

  const platformDescription =
    typeof platform === "object" ? platform?.description || "" : "";

  // ==========================================================
  // PLATFORM COLORS
  // ==========================================================

  const platformBackgroundColor =
    backgroundColor ||
    (typeof platform === "object" ? platform?.backgroundColor : "") ||
    "#F1F5F9";

  const platformIconColor =
    iconColor ||
    (typeof platform === "object"
      ? platform?.color || platform?.iconColor
      : "") ||
    "#475569";

  // ==========================================================
  // COMING SOON
  // ==========================================================

  const comingSoon =
    typeof platform === "object" && Boolean(platform?.comingSoon);

  // ==========================================================
  // ICON
  // ==========================================================

  const Icon = PLATFORM_ICONS[platformId] || ApartmentRoundedIcon;

  // ==========================================================
  // CONNECT HANDLER
  // ==========================================================

  const handleConnect = () => {
    if (disabled || loading || comingSoon || typeof onConnect !== "function") {
      return;
    }

    onConnect(platform);
  };

  // ==========================================================
  // ACCESSIBILITY LABEL
  // ==========================================================

  const connectLabel = comingSoon
    ? `${platformName} coming soon`
    : connected
      ? `Reconnect ${platformName}`
      : `Connect ${platformName}`;

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <Box
      component="article"
      sx={{
        flex: overviewStyle ? "1 1 0" : "1 1 180px",

        minWidth: overviewStyle ? 0 : { xs: 160, sm: 180 },

        maxWidth: overviewStyle ? "none" : 210,

        minHeight: overviewStyle ? 166 : 150,
        height: overviewStyle ? "100%" : undefined,

        p: overviewStyle ? 1.5 : 2,

        borderRadius: "16px",

        border: "1px solid rgba(255,255,255,.95)",

        background: "linear-gradient(145deg, rgba(250,252,255,.96), rgba(235,243,255,.88))",
        boxShadow: "0 7px 16px rgba(75,96,151,.1), inset 0 0 0 1px rgba(177,196,227,.12), inset 0 2px 0 rgba(255,255,255,.98)",

        display: "flex",

        flexDirection: "column",

        alignItems: "center",

        justifyContent: "center",

        textAlign: "center",

        transition:
          "border-color .2s ease, box-shadow .2s ease, transform .2s ease",

        opacity: disabled ? 0.55 : 1,

        ...(overviewStyle ? overviewGlassCardSx : {}),

        "&:hover": disabled
          ? {}
          : {
              borderColor: "rgba(140,166,211,.7)",
              background: "linear-gradient(145deg, rgba(240,247,255,.98), rgba(228,239,255,.94))",
              transform: "translateY(-2px)",
              boxShadow: "0 10px 20px rgba(75,96,151,.15), inset 0 2px 0 rgba(255,255,255,.98)",
            },
      }}
    >
      {/* ======================================================
          PLATFORM ICON
      ====================================================== */}

      <Box
        sx={{
          width: 44,
          height: 44,
          borderRadius: "12px",

          bgcolor: platformBackgroundColor,
          border: "1px solid rgba(255,255,255,.94)",
          boxShadow: "0 4px 10px rgba(75,96,151,.08), inset 0 2px 2px rgba(255,255,255,.82)",

          display: "flex",
          alignItems: "center",
          justifyContent: "center",

          mb: 1.25,
        }}
      >
        <Icon
          aria-hidden="true"
          sx={{
            fontSize: 23,
            color: platformIconColor,
          }}
        />
      </Box>

      {/* ======================================================
          PLATFORM NAME
      ====================================================== */}

      <Typography
        component="p"
        sx={{
          fontSize: 14,
          fontWeight: 600,
          color: "#334155",
          lineHeight: 1.4,
          mb: platformDescription ? 0.35 : 1.25,
        }}
      >
        {platformName}
      </Typography>

      {/* ======================================================
          PLATFORM DESCRIPTION
      ====================================================== */}

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

      {/* ======================================================
          CONNECT BUTTON
      ====================================================== */}

      <Button
        type="button"
        variant="outlined"
        size="small"
        onClick={handleConnect}
        disabled={
          disabled || loading || comingSoon || typeof onConnect !== "function"
        }
        aria-label={connectLabel}
        aria-busy={loading}
        sx={{
          minWidth: overviewStyle ? 0 : 105,
          width: overviewStyle ? "100%" : undefined,
          height: 34,

          px: overviewStyle ? 0.75 : 1.5,

          borderRadius: "10px",

          borderColor: "rgba(165,183,211,.72)",

          color: "#475569",

          textTransform: "none",

          fontSize: overviewStyle ? 12 : 13,

          fontWeight: 600,

          boxShadow: "0 3px 8px rgba(75,96,151,.07), inset 0 1px 0 rgba(255,255,255,.98)",

          "&:hover": {
            borderColor: "rgba(116,150,208,.72)",
            color: "#2563EB",
            background: "linear-gradient(145deg, rgba(240,247,255,.98), rgba(228,239,255,.94))",
            boxShadow: "0 5px 10px rgba(75,96,151,.1), inset 0 1px 0 rgba(255,255,255,.98)",
          },

          "&.Mui-disabled": {
            borderColor: "#E2E8F0",
            color: "#94A3B8",
            bgcolor: "transparent",
          },
        }}
      >
        {loading
          ? "Connecting..."
          : comingSoon
            ? "Coming soon"
            : connected
              ? "Reconnect"
              : "Connect"}
      </Button>
    </Box>
  );
}
