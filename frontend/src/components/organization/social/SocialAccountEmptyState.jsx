// import { Box, Button, Typography } from "@mui/material";
// import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";

// // ============================================================
// // SOCIAL ACCOUNT EMPTY STATE
// // ============================================================
// //
// // Reusable empty-state component.
// //
// // Used when an organization has no connected social accounts.
// //
// // This component is UI-only.
// // It does not:
// // - fetch API data
// // - perform OAuth
// // - know organization details
// // - contain platform-specific logic
// //
// // Parent component decides what should happen when the user
// // clicks "Connect an account".
// //
// // ============================================================

// export default function SocialAccountEmptyState({
//   title = "No accounts connected yet",
//   description = "Connect this organization's social accounts to start publishing and managing social activity.",
//   actionLabel = "Connect an account",
//   showAction = false,
//   onAction,
//   disabled = false,
// }) {
//   // ============================================================
//   // ACTION
//   // ============================================================

//   const handleAction = () => {
//     if (disabled || typeof onAction !== "function") {
//       return;
//     }

//     onAction();
//   };

//   // ============================================================
//   // RENDER
//   // ============================================================

//   return (
//     <Box
//       sx={{
//         minHeight: 190,

//         px: {
//           xs: 2,
//           sm: 3,
//         },

//         py: 4,

//         border: "1px dashed #CBD5E1",

//         borderRadius: "18px",

//         bgcolor: "#FFFFFF",

//         display: "flex",

//         flexDirection: "column",

//         alignItems: "center",

//         justifyContent: "center",

//         textAlign: "center",
//       }}
//     >
//       {/* ======================================================
//           ICON
//       ====================================================== */}

//       <Box
//         sx={{
//           width: 50,

//           height: 50,

//           borderRadius: "14px",

//           bgcolor: "#F1F5F9",

//           display: "flex",

//           alignItems: "center",

//           justifyContent: "center",

//           mb: 2,
//         }}
//       >
//         <ShareOutlinedIcon
//           sx={{
//             fontSize: 24,

//             color: "#64748B",
//           }}
//         />
//       </Box>

//       {/* ======================================================
//           TITLE
//       ====================================================== */}

//       <Typography
//         sx={{
//           fontSize: 16,

//           fontWeight: 600,

//           color: "#1E293B",

//           lineHeight: 1.4,
//         }}
//       >
//         {title}
//       </Typography>

//       {/* ======================================================
//           DESCRIPTION
//       ====================================================== */}

//       <Typography
//         sx={{
//           mt: 0.75,

//           maxWidth: 540,

//           fontSize: 14,

//           lineHeight: 1.6,

//           color: "#64748B",
//         }}
//       >
//         {description}
//       </Typography>

//       {/* ======================================================
//           OPTIONAL ACTION
//       ====================================================== */}

//       {showAction && (
//         <Button
//           type="button"
//           variant="outlined"
//           onClick={handleAction}
//           disabled={disabled || typeof onAction !== "function"}
//           sx={{
//             mt: 2.5,

//             minWidth: 150,

//             height: 38,

//             px: 2,

//             borderRadius: "10px",

//             borderColor: "#CBD5E1",

//             color: "#475569",

//             textTransform: "none",

//             fontSize: 13,

//             fontWeight: 600,

//             boxShadow: "none",

//             "&:hover": {
//               borderColor: "#2563EB",

//               color: "#2563EB",

//               bgcolor: "#F8FBFF",

//               boxShadow: "none",
//             },

//             "&.Mui-disabled": {
//               borderColor: "#E2E8F0",

//               color: "#94A3B8",
//             },
//           }}
//         >
//           {actionLabel}
//         </Button>
//       )}
//     </Box>
//   );
// }

import { Box, Button, Typography } from "@mui/material";
import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";

// ============================================================
// SOCIAL ACCOUNT EMPTY STATE
// ============================================================
//
// Reusable empty-state component.
//
// Used when an organization has no connected social accounts.
//
// This component is UI-only.
// It does not:
// - fetch API data
// - perform OAuth
// - know organization details
// - contain platform-specific logic
//
// Parent component decides what should happen when the user
// clicks "Connect an account".
//
// ============================================================

export default function SocialAccountEmptyState({
  title = "No accounts connected yet",
  description = "Connect this organization's social accounts to start publishing and managing social activity.",
  actionLabel = "Connect an account",
  showAction = false,
  onAction,
  disabled = false,
}) {
  // ============================================================
  // ACTION
  // ============================================================

  const handleAction = () => {
    if (disabled || typeof onAction !== "function") {
      return;
    }

    onAction();
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <Box
      role="region"
      aria-label={title}
      sx={{
        minHeight: 190,

        px: {
          xs: 2,
          sm: 3,
        },

        py: 4,

        border: "1px dashed #CBD5E1",

        borderRadius: "18px",

        bgcolor: "#FFFFFF",

        display: "flex",

        flexDirection: "column",

        alignItems: "center",

        justifyContent: "center",

        textAlign: "center",
      }}
    >
      {/* ======================================================
          ICON
      ====================================================== */}

      <Box
        aria-hidden="true"
        sx={{
          width: 50,

          height: 50,

          borderRadius: "14px",

          bgcolor: "#F1F5F9",

          display: "flex",

          alignItems: "center",

          justifyContent: "center",

          mb: 2,
        }}
      >
        <ShareOutlinedIcon
          sx={{
            fontSize: 24,

            color: "#64748B",
          }}
        />
      </Box>

      {/* ======================================================
          TITLE
      ====================================================== */}

      <Typography
        component="h3"
        sx={{
          fontSize: 16,

          fontWeight: 600,

          color: "#1E293B",

          lineHeight: 1.4,

          m: 0,
        }}
      >
        {title}
      </Typography>

      {/* ======================================================
          DESCRIPTION
      ====================================================== */}

      <Typography
        sx={{
          mt: 0.75,

          maxWidth: 540,

          fontSize: 14,

          lineHeight: 1.6,

          color: "#64748B",
        }}
      >
        {description}
      </Typography>

      {/* ======================================================
          OPTIONAL ACTION
      ====================================================== */}

      {showAction && (
        <Button
          type="button"
          variant="outlined"
          onClick={handleAction}
          disabled={disabled || typeof onAction !== "function"}
          sx={{
            mt: 2.5,

            minWidth: 150,

            height: 38,

            px: 2,

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
            },
          }}
        >
          {actionLabel}
        </Button>
      )}
    </Box>
  );
}
