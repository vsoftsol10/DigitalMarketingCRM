// import { Box, Stack, Typography } from "@mui/material";

// import AccessTimeRoundedIcon from "@mui/icons-material/AccessTimeRounded";
// import FiberManualRecordRoundedIcon from "@mui/icons-material/FiberManualRecordRounded";

// import { TYPOGRAPHY } from "../../theme/typography";

// export default function CalendarEvent({
//   event,
//   onClick,
// }) {
//   if (!event) {
//     return null;
//   }

//   const {
//     title,
//     time,
//     platform,
//     contentType,
//     status,
//     color,
//     backgroundColor,
//   } = event;

//   return (
//     <Box
//       component="button"
//       type="button"
//       onClick={() => onClick?.(event)}
//       sx={{
//         width: "100%",

//         border: "none",
//         borderLeft: "3px solid",

//         borderColor:
//           color || "primary.main",

//         borderRadius: 1.5,

//         bgcolor:
//           backgroundColor ||
//           "action.hover",

//         px: 1,
//         py: 0.75,

//         textAlign: "left",

//         cursor: "pointer",

//         overflow: "hidden",

//         transition:
//           "background-color 0.2s ease, transform 0.15s ease",

//         "&:hover": {
//           bgcolor: "action.selected",
//         },

//         "&:active": {
//           transform: "translateY(1px)",
//         },

//         "&:focus-visible": {
//           outline: "2px solid",
//           outlineColor: "primary.main",
//           outlineOffset: 1,
//         },
//       }}
//     >
//       {/* Time */}

//       {time && (
//         <Stack
//           direction="row"
//           alignItems="center"
//           spacing={0.5}
//           sx={{
//             minWidth: 0,
//           }}
//         >
//           <AccessTimeRoundedIcon
//             sx={{
//               fontSize: 13,
//               color: "text.secondary",
//               flexShrink: 0,
//             }}
//           />

//           <Typography
//             noWrap
//             sx={{
//               ...TYPOGRAPHY.caption,
//               fontWeight: 600,
//               color: "text.primary",
//             }}
//           >
//             {time}
//           </Typography>
//         </Stack>
//       )}

//       {/* Title */}

//       {title && (
//         <Typography
//           noWrap
//           sx={{
//             ...TYPOGRAPHY.caption,

//             fontWeight: 600,

//             color: "text.primary",

//             mt: time ? 0.25 : 0,
//           }}
//         >
//           {title}
//         </Typography>
//       )}

//       {/* Metadata */}

//       {(platform ||
//         contentType ||
//         status) && (
//         <Stack
//           direction="row"
//           alignItems="center"
//           spacing={0.75}
//           sx={{
//             mt: 0.5,

//             minWidth: 0,

//             overflow: "hidden",
//           }}
//         >
//           {platform && (
//             <Typography
//               noWrap
//               sx={{
//                 ...TYPOGRAPHY.caption,

//                 color:
//                   "text.secondary",

//                 overflow: "hidden",

//                 textOverflow:
//                   "ellipsis",
//               }}
//             >
//               {platform}
//             </Typography>
//           )}

//           {platform &&
//             (contentType ||
//               status) && (
//               <FiberManualRecordRoundedIcon
//                 sx={{
//                   fontSize: 4,
//                   color:
//                     "text.disabled",
//                   flexShrink: 0,
//                 }}
//               />
//             )}

//           {contentType && (
//             <Typography
//               noWrap
//               sx={{
//                 ...TYPOGRAPHY.caption,

//                 color:
//                   "text.secondary",

//                 overflow: "hidden",

//                 textOverflow:
//                   "ellipsis",
//               }}
//             >
//               {contentType}
//             </Typography>
//           )}

//           {contentType &&
//             status && (
//               <FiberManualRecordRoundedIcon
//                 sx={{
//                   fontSize: 4,
//                   color:
//                     "text.disabled",
//                   flexShrink: 0,
//                 }}
//               />
//             )}

//           {status && (
//             <Typography
//               noWrap
//               sx={{
//                 ...TYPOGRAPHY.caption,

//                 color:
//                   "text.secondary",

//                 overflow: "hidden",

//                 textOverflow:
//                   "ellipsis",
//               }}
//             >
//               {status}
//             </Typography>
//           )}
//         </Stack>
//       )}
//     </Box>
//   );
// }

import {
  Box,
  Stack,
  Typography,
} from "@mui/material";

import AccessTimeRoundedIcon from "@mui/icons-material/AccessTimeRounded";
import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import YouTubeIcon from "@mui/icons-material/YouTube";
import LanguageRoundedIcon from "@mui/icons-material/LanguageRounded";
import XIcon from "@mui/icons-material/X";

import { TYPOGRAPHY } from "../../theme/typography";

// ==========================================
// PLATFORM CONFIG
// ==========================================
//
// UI-only configuration. Backend sends platform as an
// uppercase string, e.g. platform: "INSTAGRAM" — but we
// normalize with .toUpperCase() below anyway so this never
// silently falls back just because of casing.
//
// `color` is the platform's brand color. In this dense grid
// we use it sparingly — just to tint the icon — rather than
// a filled badge, so a day with many events doesn't turn into
// a wall of colour.

const PLATFORM_CONFIG = {
  INSTAGRAM: {
    label: "Instagram",
    shortLabel: "Instagram",
    icon: InstagramIcon,
    color: "#E1306C",
  },

  FACEBOOK: {
    label: "Facebook",
    shortLabel: "Facebook",
    icon: FacebookRoundedIcon,
    color: "#1877F2",
  },

  LINKEDIN: {
    label: "LinkedIn",
    shortLabel: "LinkedIn",
    icon: LinkedInIcon,
    color: "#0A66C2",
  },

  YOUTUBE: {
    label: "YouTube",
    shortLabel: "YouTube",
    icon: YouTubeIcon,
    color: "#FF0000",
  },

  X: {
    label: "X",
    shortLabel: "X",
    icon: XIcon,
    color: "#0F1419",
  },

  THREADS: {
    label: "Threads",
    shortLabel: "Threads",
    icon: LanguageRoundedIcon,
    color: "#000000",
  },

  DEFAULT: {
    label: "Platform",
    shortLabel: "Platform",
    icon: LanguageRoundedIcon,
    color: null,
  },
};

// ==========================================
// STATUS CONFIG
// ==========================================
//
// `dot` is the color of the small status indicator. Kept
// separate from a text-color map so both the dot and any
// future badge/chip can read from one place.

const STATUS_CONFIG = {
  DRAFT: {
    label: "Draft",
    dot: "text.disabled",
  },

  SCHEDULED: {
    label: "Scheduled",
    dot: "primary.main",
  },

  PUBLISHED: {
    label: "Published",
    dot: "success.main",
  },

  FAILED: {
    label: "Failed",
    dot: "error.main",
  },

  DEFAULT: {
    label: "Unknown",
    dot: "text.disabled",
  },
};

export default function CalendarEvent({
  event,
  onClick,
}) {
  if (!event) {
    return null;
  }

  const {
    title,
    time,
    platform,
    contentType,
    status,
    color,
    backgroundColor,
  } = event;

  // ==========================================
  // PLATFORM
  // Normalize casing so "instagram" / "Instagram" /
  // "INSTAGRAM" all resolve the same way instead of
  // silently falling through to DEFAULT.
  // ==========================================

  const platformKey = platform
    ?.toString()
    .trim()
    .toUpperCase();

  const platformConfig =
    PLATFORM_CONFIG[platformKey] ||
    PLATFORM_CONFIG.DEFAULT;

  const PlatformIcon = platformConfig.icon;

  // ==========================================
  // STATUS
  // Same normalization as platform, so the status dot
  // and label never mismatch due to casing.
  // ==========================================

  const statusKey = status
    ?.toString()
    .trim()
    .toUpperCase();

  const statusConfig = status
    ? STATUS_CONFIG[statusKey] || {
        label: status,
        dot: STATUS_CONFIG.DEFAULT.dot,
      }
    : null;

  return (
    <Box
      component="button"
      type="button"
      onClick={() => onClick?.(event)}
      aria-label={`${title || "Calendar event"} - ${
        platformConfig.label
      }`}
      sx={{
        width: "100%",
        minWidth: 0,
        border: "none",
        borderLeft: "3px solid",
        borderColor: color || "primary.main",
        borderRadius: 1.75,
        bgcolor: backgroundColor || "action.hover",
        px: 1,
        py: 0.9,
        textAlign: "left",
        cursor: "pointer",
        overflow: "hidden",
        boxSizing: "border-box",
        transition:
          "background-color 0.2s ease, box-shadow 0.2s ease, transform 0.15s ease",

        "&:hover": {
          bgcolor: backgroundColor || "action.selected",
          boxShadow: "0 2px 8px rgba(15, 23, 42, 0.08)",
        },

        "&:active": {
          transform: "translateY(1px)",
        },

        "&:focus-visible": {
          outline: "2px solid",
          outlineColor: "primary.main",
          outlineOffset: 1,
        },
      }}
    >
      {/* ==========================================
          TOP ROW — time + platform
      ========================================== */}

      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        spacing={0.75}
        sx={{ width: "100%", minWidth: 0 }}
      >
        {time && (
          <Stack
            direction="row"
            alignItems="center"
            spacing={0.4}
            sx={{ minWidth: 0 }}
          >
            <AccessTimeRoundedIcon
              sx={{
                fontSize: 13,
                color: "text.secondary",
                flexShrink: 0,
              }}
            />

            <Typography
              noWrap
              sx={{
                ...TYPOGRAPHY.caption,
                fontWeight: 700,
                color: "text.primary",
              }}
            >
              {time}
            </Typography>
          </Stack>
        )}

        {platform && (
          <Stack
            direction="row"
            alignItems="center"
            spacing={0.4}
            sx={{
              minWidth: 0,
              flexShrink: 0,
              maxWidth: "50%",
            }}
          >
            <PlatformIcon
              sx={{
                fontSize: 14,
                color:
                  platformConfig.color ||
                  "text.secondary",
                flexShrink: 0,
              }}
            />

            <Typography
              noWrap
              sx={{
                ...TYPOGRAPHY.caption,
                fontWeight: 600,
                color: "text.secondary",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {platformConfig.shortLabel}
            </Typography>
          </Stack>
        )}
      </Stack>

      {/* ==========================================
          TITLE
      ========================================== */}

      {title && (
        <Typography
          noWrap
          sx={{
            ...TYPOGRAPHY.caption,
            fontWeight: 700,
            color: "text.primary",
            mt: 0.65,
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {title}
        </Typography>
      )}

      {/* ==========================================
          CONTENT TYPE + STATUS
      ========================================== */}

      {(contentType || statusConfig) && (
        <Stack
          direction="row"
          alignItems="center"
          spacing={0.5}
          sx={{
            mt: 0.5,
            minWidth: 0,
            overflow: "hidden",
          }}
        >
          {contentType && (
            <Typography
              noWrap
              sx={{
                ...TYPOGRAPHY.caption,
                fontWeight: 500,
                color: "text.secondary",
                textTransform: "capitalize",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {contentType.toLowerCase()}
            </Typography>
          )}

          {contentType && statusConfig && (
            <Box
              component="span"
              sx={{
                width: 3,
                height: 3,
                borderRadius: "50%",
                bgcolor: "text.disabled",
                flexShrink: 0,
              }}
            />
          )}

          {statusConfig && (
            <Stack
              direction="row"
              alignItems="center"
              spacing={0.4}
              sx={{ minWidth: 0 }}
            >
              <Box
                component="span"
                sx={{
                  width: 5,
                  height: 5,
                  borderRadius: "50%",
                  bgcolor: statusConfig.dot,
                  flexShrink: 0,
                }}
              />

              <Typography
                noWrap
                sx={{
                  ...TYPOGRAPHY.caption,
                  fontWeight: 600,
                  color: "text.secondary",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {statusConfig.label}
              </Typography>
            </Stack>
          )}
        </Stack>
      )}
    </Box>
  );
}