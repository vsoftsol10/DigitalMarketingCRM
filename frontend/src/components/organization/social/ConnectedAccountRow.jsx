import { memo, useState } from "react";

import {
  Avatar,
  Box,
  Button,
  Chip,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";

import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import YouTubeIcon from "@mui/icons-material/YouTube";

// ============================================================
// PLATFORM ICONS
// ============================================================

const PLATFORM_ICONS = {
  instagram: InstagramIcon,
  facebook: FacebookRoundedIcon,
  linkedin: LinkedInIcon,
  youtube: YouTubeIcon,
};

// ============================================================
// PLATFORM NAMES
// ============================================================

const PLATFORM_NAMES = {
  instagram: "Instagram",
  facebook: "Facebook",
  linkedin: "LinkedIn",
  youtube: "YouTube",
};

// ============================================================
// ACCOUNT TYPES
// ============================================================
//
// These describe what the connected account represents.
// They are derived from the platform, not from account data.
//
// ============================================================

const ACCOUNT_TYPES = {
  facebook: "Facebook Page",
  instagram: "Instagram Professional Account",
  linkedin: "LinkedIn Account",
  youtube: "YouTube Channel",
};

// ============================================================
// DATE FORMATTER
// ============================================================

function formatLastSync(value) {
  if (!value) {
    return "Not synced yet";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return `Last synced ${date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })}`;
}

// ============================================================
// SHARED PILL HEIGHT
// ============================================================

const PILL_HEIGHT = 32;

// ============================================================
// COMPONENT
// ============================================================

function ConnectedAccountRow({
  account,
  onReconnect,
  onDisconnect,
  loading = false,
}) {
  const [imgError, setImgError] = useState(false);
  const [actionError, setActionError] = useState("");

  // ==========================================================
  // ACCOUNT DATA
  // ==========================================================

  const platform = account?.platform || "";

  const Icon = PLATFORM_ICONS[platform];

  const platformName =
    PLATFORM_NAMES[platform] ||
    (platform
      ? platform.charAt(0).toUpperCase() + platform.slice(1)
      : "Social Account");

  const accountType = ACCOUNT_TYPES[platform] || "Social Media Account";

  // ==========================================================
  // DISPLAY IDENTITY
  // ==========================================================
  //
  // Facebook:
  //     accountName = Page name
  //
  // Instagram:
  //     accountName = Instagram profile name
  //     username    = Instagram username
  //
  // No actual account name is hardcoded here.
  //
  // ==========================================================

  const accountName =
    account?.accountName || account?.pageName || account?.name || platformName;

  const username = account?.username || "";

  const connected = Boolean(account?.connected);

  const valid = account?.valid !== false;

  const profileImage =
    !imgError && account?.profileImage ? account.profileImage : "";

  const lastSync = account?.lastSync || null;

  // ==========================================================
  // RECONNECT
  // ==========================================================

  const handleReconnect = async () => {
    if (loading || typeof onReconnect !== "function") {
      return;
    }

    setActionError("");

    try {
      await onReconnect(account);
    } catch (err) {
      setActionError("Reconnect failed. Try again.");
    }
  };

  // ==========================================================
  // DISCONNECT
  // ==========================================================

  const handleDisconnect = async () => {
    if (loading || typeof onDisconnect !== "function") {
      return;
    }

    setActionError("");

    try {
      await onDisconnect(account);
    } catch (err) {
      setActionError("Disconnect failed. Try again.");
    }
  };

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <Box
      sx={{
        mt: 2,
        px: {
          xs: 2,
          sm: 2.5,
        },
        py: 2,
        border: "1px solid #E2E8F0",
        borderRadius: "18px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: {
          xs: "flex-start",
          md: "center",
        },
        gap: 2,
        flexDirection: {
          xs: "column",
          md: "row",
        },
        transition: "border-color .2s ease, box-shadow .2s ease",
        "&:hover": {
          borderColor: "#CBD5E1",
          boxShadow: "0 8px 20px rgba(15,23,42,.05)",
        },
      }}
    >
      {/* ======================================================
          LEFT
      ====================================================== */}

      <Stack
        direction="row"
        spacing={2}
        alignItems="center"
        minWidth={0}
        width="100%"
      >
        {/* ==================================================
            PROFILE / PLATFORM AVATAR
        ================================================== */}

        <Avatar
          src={profileImage || undefined}
          alt={accountName}
          onError={() => setImgError(true)}
          sx={{
            width: 50,
            height: 50,
            bgcolor: "#F8FAFC",
            color: "#111827",
            border: "1px solid #E2E8F0",
            flexShrink: 0,
          }}
        >
          {!profileImage && Icon && (
            <Icon
              sx={{
                color: "#111827",
                fontSize: 23,
              }}
            />
          )}
        </Avatar>

        {/* ==================================================
            ACCOUNT INFORMATION
        ================================================== */}

        <Box
          sx={{
            minWidth: 0,
            flex: 1,
          }}
        >
          {/* ================================================
              ACCOUNT NAME
          ================================================= */}

          <Typography
            component="h4"
            sx={{
              fontSize: 16,
              fontWeight: 600,
              color: "#1E293B",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              m: 0,
            }}
          >
            {accountName}
          </Typography>

          {/* ================================================
              USERNAME / PLATFORM
          ================================================= */}

          <Typography
            sx={{
              mt: 0.35,
              fontSize: 13,
              color: "#64748B",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {username
              ? platform === "instagram"
                ? `@${username}`
                : username
              : platformName}
          </Typography>

          {/* ================================================
              ACCOUNT TYPE
          ================================================= */}

          <Typography
            sx={{
              mt: 0.25,
              fontSize: 12,
              fontWeight: 500,
              color: "#94A3B8",
            }}
          >
            {accountType}
          </Typography>

          {/* ================================================
              LAST SYNC
          ================================================= */}

          <Typography
            sx={{
              mt: 0.25,
              fontSize: 12,
              color: "#94A3B8",
            }}
          >
            {formatLastSync(lastSync)}
          </Typography>

          {/* ================================================
              ACTION ERROR
          ================================================= */}

          {actionError && (
            <Typography
              sx={{
                mt: 0.4,
                fontSize: 12,
                color: "#DC2626",
              }}
            >
              {actionError}
            </Typography>
          )}
        </Box>
      </Stack>

      {/* ======================================================
          RIGHT ACTION AREA
      ====================================================== */}

      <Stack
        direction="row"
        spacing={1.25}
        alignItems="center"
        justifyContent="flex-end"
        flexShrink={0}
        sx={{
          width: {
            xs: "100%",
            md: "auto",
          },
          ml: {
            md: 2,
          },
        }}
      >
        {/* ==================================================
            CONNECTION STATUS
        ================================================== */}

        <Chip
          label={connected ? "Connected" : "Disconnected"}
          size="small"
          sx={{
            height: PILL_HEIGHT,
            display: "flex",
            alignItems: "center",
            bgcolor: connected ? "#ECFDF3" : "#F1F5F9",
            color: connected ? "#059669" : "#64748B",
            border: "1px solid",
            borderColor: connected ? "#A7F3D0" : "#CBD5E1",
            fontWeight: 600,
            fontSize: 12,
            "& .MuiChip-label": {
              lineHeight: 1,
              px: "10px",
            },
          }}
        />

        {/* ==================================================
            VALIDITY STATUS
        ================================================== */}

        <Chip
          label={valid ? "Valid" : "Expired"}
          size="small"
          sx={{
            height: PILL_HEIGHT,
            display: "flex",
            alignItems: "center",
            bgcolor: valid ? "#ECFDF3" : "#FEF2F2",
            color: valid ? "#059669" : "#DC2626",
            border: "1px solid",
            borderColor: valid ? "#A7F3D0" : "#FECACA",
            fontWeight: 600,
            fontSize: 12,
            "& .MuiChip-label": {
              lineHeight: 1,
              px: "10px",
            },
          }}
        />

        {/* ==================================================
            SEPARATOR
        ================================================== */}

        <Box
          sx={{
            width: "1px",
            height: 20,
            bgcolor: "#E2E8F0",
            display: {
              xs: "none",
              md: "block",
            },
          }}
        />

        {/* ==================================================
            RECONNECT / DISCONNECT
        ================================================== */}

        {!connected || !valid ? (
          <Button
            type="button"
            variant="outlined"
            size="small"
            onClick={handleReconnect}
            disabled={loading || typeof onReconnect !== "function"}
            aria-label={`Reconnect ${accountName}`}
            startIcon={
              loading ? <CircularProgress size={14} color="inherit" /> : null
            }
            sx={{
              height: PILL_HEIGHT,
              minWidth: 92,
              borderRadius: "10px",
              borderColor: "#CBD5E1",
              color: "#475569",
              textTransform: "none",
              fontSize: 13,
              fontWeight: 600,
              lineHeight: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              "&:hover": {
                borderColor: "#2563EB",
                color: "#2563EB",
                bgcolor: "#F8FBFF",
              },
            }}
          >
            {loading ? "Connecting..." : "Reconnect"}
          </Button>
        ) : (
          <Button
            type="button"
            variant="text"
            size="small"
            onClick={handleDisconnect}
            disabled={loading || typeof onDisconnect !== "function"}
            aria-label={`Disconnect ${accountName}`}
            startIcon={
              loading ? <CircularProgress size={14} color="inherit" /> : null
            }
            sx={{
              height: PILL_HEIGHT,
              minWidth: 92,
              borderRadius: "10px",
              color: "#64748B",
              textTransform: "none",
              fontSize: 13,
              fontWeight: 600,
              lineHeight: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              px: 1.5,
              "&:hover": {
                color: "#DC2626",
                bgcolor: "#FEF2F2",
              },
            }}
          >
            {loading ? "Please wait..." : "Disconnect"}
          </Button>
        )}
      </Stack>
    </Box>
  );
}

export default memo(ConnectedAccountRow);
