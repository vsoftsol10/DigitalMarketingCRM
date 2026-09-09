import { Box, Checkbox, Stack, Typography } from "@mui/material";

import CheckRoundedIcon from "@mui/icons-material/CheckRounded";

import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import YouTubeIcon from "@mui/icons-material/YouTube";

import { TYPOGRAPHY } from "../../../theme/typography";

// ============================================================
// PLATFORM ICONS
// ============================================================

const PLATFORM_ICONS = {
  INSTAGRAM: InstagramIcon,
  FACEBOOK: FacebookRoundedIcon,
  LINKEDIN: LinkedInIcon,
  YOUTUBE: YouTubeIcon,
};

// ============================================================
// PLATFORM STYLES
// ============================================================

const PLATFORM_STYLES = {
  INSTAGRAM: {
    backgroundColor: "#FCE7F3",
    iconColor: "#E1306C",
  },

  FACEBOOK: {
    backgroundColor: "#EFF6FF",
    iconColor: "#1877F2",
  },

  LINKEDIN: {
    backgroundColor: "#EFF6FF",
    iconColor: "#0A66C2",
  },

  YOUTUBE: {
    backgroundColor: "#FEF2F2",
    iconColor: "#FF0000",
  },
};

// ============================================================
// COMPONENT
// ============================================================

export default function SocialAccountCard({
  account,
  selected = false,
  disabled = false,
  statusText = "",
  onChange,
}) {
  // ==========================================================
  // ACCOUNT VALIDATION
  // ==========================================================

  if (!account?.id) {
    return null;
  }

  // ==========================================================
  // PLATFORM
  // ==========================================================

  const platform = account?.platform || "";

  const Icon = PLATFORM_ICONS[platform];

  const platformStyle = PLATFORM_STYLES[platform] || {
    backgroundColor: "#F1F5F9",
    iconColor: "#475569",
  };

  // ==========================================================
  // ACCOUNT INFORMATION
  // ==========================================================

  const accountName =
    account?.accountName ||
    account?.pageName ||
    account?.name ||
    "Social account";

  const username = account?.username || "";

  // ==========================================================
  // ACCOUNT SELECTION
  // ==========================================================

  function handleChange() {
    if (disabled) {
      return;
    }

    if (typeof onChange !== "function") {
      return;
    }

    onChange(account.id);
  }

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <Box
      component="button"
      type="button"
      onClick={handleChange}
      disabled={disabled}
      aria-pressed={selected}
      aria-label={
        selected ? `Selected ${accountName}` : `Select ${accountName}`
      }
      sx={{
        width: "100%",

        minHeight: 72,

        p: 1.25,

        border: "1px solid",

        borderColor: selected ? "primary.main" : "divider",

        borderRadius: "14px",

        bgcolor: selected ? "action.selected" : "background.paper",

        textAlign: "left",

        fontFamily: "inherit",

        cursor: disabled ? "not-allowed" : "pointer",

        opacity: disabled ? 0.6 : 1,

        transition:
          "border-color .2s ease, background-color .2s ease, box-shadow .2s ease",

        "&:hover": disabled
          ? {}
          : {
              borderColor: "primary.main",

              bgcolor: "action.hover",

              boxShadow: "0 3px 12px rgba(15, 23, 42, 0.05)",
            },

        "&:focus-visible": {
          outline: "2px solid",

          outlineColor: "primary.main",

          outlineOffset: 2,
        },

        "&:disabled": {
          cursor: "not-allowed",
        },
      }}
    >
      <Stack direction="row" alignItems="center" spacing={1.25}>
        {/* ====================================================
            PLATFORM ICON
        ==================================================== */}

        <Box
          sx={{
            width: 38,

            height: 38,

            borderRadius: "10px",

            bgcolor: platformStyle.backgroundColor,

            display: "flex",

            alignItems: "center",

            justifyContent: "center",

            flexShrink: 0,
          }}
        >
          {Icon && (
            <Icon
              sx={{
                fontSize: 20,

                color: platformStyle.iconColor,
              }}
            />
          )}
        </Box>

        {/* ====================================================
            ACCOUNT INFORMATION
        ==================================================== */}

        <Box
          sx={{
            flex: 1,

            minWidth: 0,
          }}
        >
          <Typography
            sx={{
              ...TYPOGRAPHY.cardTitle,

              fontSize: 13.5,

              fontWeight: 600,

              lineHeight: 1.35,

              color: "text.primary",

              overflow: "hidden",

              textOverflow: "ellipsis",

              whiteSpace: "nowrap",
            }}
          >
            {accountName}
          </Typography>

          {username && (
            <Typography
              sx={{
                ...TYPOGRAPHY.bodySmall,

                mt: 0.2,

                fontSize: 11.5,

                lineHeight: 1.35,

                color: "text.secondary",

                overflow: "hidden",

                textOverflow: "ellipsis",

                whiteSpace: "nowrap",
              }}
            >
              {username}
            </Typography>
          )}

          {statusText && (
            <Typography
              sx={{
                mt: 0.25,

                fontSize: 10.5,

                lineHeight: 1.3,

                color: "text.secondary",

                overflow: "hidden",

                textOverflow: "ellipsis",

                whiteSpace: "nowrap",
              }}
            >
              {statusText}
            </Typography>
          )}
        </Box>

        {/* ====================================================
            CHECKBOX
        ==================================================== */}

        <Checkbox
          checked={selected}
          disabled={disabled}
          tabIndex={-1}
          disableRipple
          onClick={(event) => {
            event.preventDefault();

            event.stopPropagation();

            handleChange();
          }}
          icon={
            <Box
              sx={{
                width: 19,

                height: 19,

                border: "1px solid #CBD5E1",

                borderRadius: "5px",
              }}
            />
          }
          checkedIcon={
            <Box
              sx={{
                width: 19,

                height: 19,

                borderRadius: "5px",

                bgcolor: "primary.main",

                color: "primary.contrastText",

                display: "flex",

                alignItems: "center",

                justifyContent: "center",
              }}
            >
              <CheckRoundedIcon
                sx={{
                  fontSize: 14,
                }}
              />
            </Box>
          }
          sx={{
            p: 0,

            flexShrink: 0,
          }}
        />
      </Stack>
    </Box>
  );
}
