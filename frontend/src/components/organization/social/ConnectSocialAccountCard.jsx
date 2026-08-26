// import { Box, Button, Typography } from "@mui/material";

// import InstagramIcon from "@mui/icons-material/Instagram";
// import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
// import LinkedInIcon from "@mui/icons-material/LinkedIn";
// import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
// import YouTubeIcon from "@mui/icons-material/YouTube";
// import XIcon from "@mui/icons-material/X";

// // ============================================================
// // PLATFORM ICONS
// // ============================================================

// const PLATFORM_ICONS = {
//   instagram: InstagramIcon,
//   facebook: FacebookRoundedIcon,
//   linkedin: LinkedInIcon,
//   threads: SmartToyOutlinedIcon,
//   youtube: YouTubeIcon,
//   x: XIcon,
// };

// // ============================================================
// // COMPONENT
// // ============================================================
// //
// // Reusable single-platform connection card.
// //
// // This component is intentionally UI-only.
// //
// // It does NOT:
// // - call the backend
// // - start OAuth
// // - know API endpoints
// // - contain organization logic
// //
// // Parent component owns the connection action.
// //
// // Example:
// //
// // <ConnectSocialAccountCard
// //   platform={platform}
// //   connected={false}
// //   onConnect={handleConnect}
// // />
// //
// // Later:
// //
// // UI
// //   ↓
// // onConnect(platform)
// //   ↓
// // OAuth service
// //   ↓
// // Backend
// //
// // ============================================================

// export default function ConnectSocialAccountCard({
//   platform,
//   name,
//   backgroundColor,
//   iconColor,

//   connected = false,

//   disabled = false,

//   loading = false,

//   onConnect,
// }) {
//   // ============================================================
//   // PLATFORM ICON
//   // ============================================================

//   const Icon = PLATFORM_ICONS[platform];

//   // ============================================================
//   // CONNECT HANDLER
//   // ============================================================

//   const handleConnect = () => {
//     if (
//       disabled ||
//       connected ||
//       loading ||
//       typeof onConnect !== "function"
//     ) {
//       return;
//     }

//     onConnect(platform);
//   };

//   // ============================================================
//   // RENDER
//   // ============================================================

//   return (
//     <Box
//       sx={{
//         flex: "1 1 150px",

//         minWidth: {
//           xs: 140,
//           sm: 150,
//         },

//         maxWidth: 170,

//         minHeight: 132,

//         p: 2,

//         borderRadius: "16px",

//         border: connected
//           ? "1px solid #A7F3D0"
//           : "1px solid #E2E8F0",

//         bgcolor: connected
//           ? "#F0FDF4"
//           : "#FFFFFF",

//         display: "flex",

//         flexDirection: "column",

//         alignItems: "center",

//         justifyContent: "center",

//         textAlign: "center",

//         transition:
//           "border-color .2s ease, box-shadow .2s ease, transform .2s ease",

//         opacity: disabled && !connected ? 0.55 : 1,

//         "&:hover":
//           disabled || connected
//             ? {}
//             : {
//                 borderColor: "#2563EB",

//                 bgcolor: "#F8FBFF",

//                 transform: "translateY(-2px)",

//                 boxShadow:
//                   "0 8px 20px rgba(15,23,42,.06)",
//               },
//       }}
//     >
//       {/* ======================================================
//           PLATFORM ICON
//       ====================================================== */}

//       <Box
//         sx={{
//           width: 44,

//           height: 44,

//           borderRadius: "12px",

//           bgcolor:
//             backgroundColor || "#F1F5F9",

//           display: "flex",

//           alignItems: "center",

//           justifyContent: "center",

//           mb: 1.25,
//         }}
//       >
//         {Icon && (
//           <Icon
//             sx={{
//               fontSize: 23,

//               color:
//                 iconColor || "#475569",
//             }}
//           />
//         )}
//       </Box>

//       {/* ======================================================
//           PLATFORM NAME
//       ====================================================== */}

//       <Typography
//         sx={{
//           fontSize: 14,

//           fontWeight: 600,

//           color: "#334155",

//           lineHeight: 1.4,

//           mb: 1.25,
//         }}
//       >
//         {name}
//       </Typography>

//       {/* ======================================================
//           ACTION
//       ====================================================== */}

//       <Button
//         type="button"
//         variant={connected ? "text" : "outlined"}
//         size="small"
//         onClick={handleConnect}
//         disabled={
//           disabled ||
//           connected ||
//           loading ||
//           typeof onConnect !== "function"
//         }
//         sx={{
//           minWidth: 100,

//           height: 34,

//           px: 1.5,

//           borderRadius: "10px",

//           borderColor: "#CBD5E1",

//           color: connected
//             ? "#059669"
//             : "#475569",

//           textTransform: "none",

//           fontSize: 13,

//           fontWeight: 600,

//           boxShadow: "none",

//           "&:hover": {
//             borderColor: "#2563EB",

//             color: "#2563EB",

//             bgcolor: "#F8FBFF",

//             boxShadow: "none",
//           },

//           "&.Mui-disabled": {
//             borderColor: connected
//               ? "#A7F3D0"
//               : "#E2E8F0",

//             color: connected
//               ? "#059669"
//               : "#94A3B8",

//             bgcolor: connected
//               ? "transparent"
//               : "transparent",
//           },
//         }}
//       >
//         {loading
//           ? "Connecting..."
//           : connected
//             ? "Connected"
//             : "Connect"}
//       </Button>
//     </Box>
//   );
// }

import { Box, Button, CircularProgress, Typography } from "@mui/material";

import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import YouTubeIcon from "@mui/icons-material/YouTube";
import XIcon from "@mui/icons-material/X";
import ApartmentRoundedIcon from "@mui/icons-material/ApartmentRounded";

// ============================================================
// PLATFORM ICONS
// ============================================================

const PLATFORM_ICONS = {
  instagram: InstagramIcon,
  facebook: FacebookRoundedIcon,
  linkedin: LinkedInIcon,
  threads: SmartToyOutlinedIcon,
  youtube: YouTubeIcon,
  x: XIcon,
};

// ============================================================
// COMPONENT
// ============================================================
//
// Reusable single-platform connection card.
//
// This component is intentionally UI-only.
//
// It does NOT:
// - call the backend
// - start OAuth
// - know API endpoints
// - contain organization logic
//
// Parent component owns the connection action.
//
// Example:
//
// <ConnectSocialAccountCard
//   platform={platform}
//   connected={false}
//   onConnect={handleConnect}
// />
//
// Later:
//
// UI
//   ↓
// onConnect(platform)
//   ↓
// OAuth service
//   ↓
// Backend
//
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
  // ============================================================
  // PLATFORM ICON
  // ============================================================
  // Falls back to a generic icon so a new/unmapped platform never
  // renders an empty box.

  const Icon = PLATFORM_ICONS[platform] || ApartmentRoundedIcon;

  const displayName = name || platform || "Social account";

  // ============================================================
  // CONNECT HANDLER
  // ============================================================

  const handleConnect = () => {
    if (disabled || connected || loading || typeof onConnect !== "function") {
      return;
    }

    onConnect(platform);
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <Box
      sx={{
        flex: "1 1 150px",

        minWidth: {
          xs: 140,
          sm: 150,
        },

        maxWidth: 170,

        minHeight: 132,

        p: 2,

        borderRadius: "16px",

        border: connected ? "1px solid #A7F3D0" : "1px solid #E2E8F0",

        bgcolor: connected ? "#F0FDF4" : "#FFFFFF",

        display: "flex",

        flexDirection: "column",

        alignItems: "center",

        justifyContent: "center",

        textAlign: "center",

        transition:
          "border-color .2s ease, box-shadow .2s ease, transform .2s ease",

        opacity: disabled && !connected ? 0.55 : 1,

        "&:hover":
          disabled || connected
            ? {}
            : {
                borderColor: "#2563EB",

                bgcolor: "#F8FBFF",

                transform: "translateY(-2px)",

                boxShadow: "0 8px 20px rgba(15,23,42,.06)",
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

          bgcolor: backgroundColor || "#F1F5F9",

          display: "flex",

          alignItems: "center",

          justifyContent: "center",

          mb: 1.25,
        }}
      >
        <Icon
          sx={{
            fontSize: 23,

            color: iconColor || "#475569",
          }}
        />
      </Box>

      {/* ======================================================
          PLATFORM NAME
      ====================================================== */}

      <Typography
        sx={{
          fontSize: 14,

          fontWeight: 600,

          color: "#334155",

          lineHeight: 1.4,

          mb: 1.25,
        }}
      >
        {displayName}
      </Typography>

      {/* ======================================================
          ACTION
      ====================================================== */}

      <Button
        type="button"
        variant={connected ? "text" : "outlined"}
        size="small"
        onClick={handleConnect}
        disabled={
          disabled || connected || loading || typeof onConnect !== "function"
        }
        aria-label={
          connected ? `${displayName} connected` : `Connect ${displayName}`
        }
        startIcon={
          loading ? <CircularProgress size={14} color="inherit" /> : null
        }
        sx={{
          minWidth: 100,

          height: 34,

          px: 1.5,

          borderRadius: "10px",

          borderColor: "#CBD5E1",

          color: connected ? "#059669" : "#475569",

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
            borderColor: connected ? "#A7F3D0" : "#E2E8F0",

            color: connected ? "#059669" : "#94A3B8",

            bgcolor: connected ? "transparent" : "transparent",
          },
        }}
      >
        {loading ? "Connecting..." : connected ? "Connected" : "Connect"}
      </Button>
    </Box>
  );
}
