// import { Alert, Box, Divider, Typography } from "@mui/material";

// import { SOCIAL_PLATFORMS } from "../../../constants/social/socialPlatforms";

// import ConnectedAccountsList from "./ConnectedAccountsList";
// import ConnectSocialAccountCard from "./ConnectSocialAccountCard";

// import useSocialAccounts from "../../../hooks/social/useSocialAccounts";

// // ============================================================
// // SOCIAL ACCOUNTS SECTION
// // ============================================================
// //
// // Single reusable Social Accounts UI.
// //
// // Used by:
// //
// // 1. Create Organization
// // 2. Edit Organization
// // 3. Organization Overview
// //
// // IMPORTANT:
// //
// // This component owns the UI composition only.
// //
// // It does NOT contain:
// // - OAuth implementation
// // - platform-specific API calls
// // - hardcoded account data
// // - organization API logic
// //
// // Platform configuration comes from:
// //
// // constants/social/socialPlatforms.js
// //
// // Account data can come from:
// //
// // 1. parent props
// // 2. useSocialAccounts hook
// //
// // This keeps the UI backend-ready while allowing dummy data
// // during the current frontend development stage.
// // ============================================================

// export default function SocialAccountsSection({
//   organizationId = null,

//   mode = "overview",

//   accounts: providedAccounts = null,

//   loading: providedLoading = false,

//   error: providedError = null,

//   onConnect,

//   onReconnect,

//   onDisconnect,

//   actionLoadingId = null,
// }) {
//   // ============================================================
//   // DETERMINE DATA SOURCE
//   // ============================================================
//   //
//   // If parent provides accounts:
//   //
//   //     use provided accounts
//   //
//   // Otherwise, when an organization ID exists:
//   //
//   //     useSocialAccounts()
//   //
//   // This allows dummy data now and backend data later.
//   // ============================================================

//   const shouldFetchAccounts =
//     providedAccounts === null && Boolean(organizationId);

//   const {
//     accounts: fetchedAccounts,
//     loading: fetchedLoading,
//     error: fetchedError,
//   } = useSocialAccounts(organizationId, {
//     enabled: shouldFetchAccounts,
//   });

//   // ============================================================
//   // RESOLVE ACCOUNTS
//   // ============================================================

//   const accounts =
//     providedAccounts !== null
//       ? Array.isArray(providedAccounts)
//         ? providedAccounts
//         : []
//       : fetchedAccounts;

//   // ============================================================
//   // RESOLVE LOADING
//   // ============================================================

//   const loading =
//     providedAccounts !== null
//       ? Boolean(providedLoading)
//       : fetchedLoading;

//   // ============================================================
//   // RESOLVE ERROR
//   // ============================================================

//   const error =
//     providedAccounts !== null
//       ? providedError
//       : fetchedError;

//   // ============================================================
//   // CONNECTED PLATFORMS
//   // ============================================================

//   const connectedPlatforms = new Set(
//     accounts
//       .filter(
//         (account) =>
//           account?.connected === true ||
//           account?.status === "connected",
//       )
//       .map((account) => account?.platform)
//       .filter(Boolean),
//   );

//   // ============================================================
//   // CREATE MODE
//   // ============================================================
//   //
//   // Organization does not exist yet.
//   //
//   // Therefore OAuth connection cannot actually start yet.
//   //
//   // But we still render the available platform UI so the user
//   // understands that social accounts are part of the setup.
//   // ============================================================

//   const isCreateMode = mode === "create";

//   // ============================================================
//   // CONNECT HANDLER
//   // ============================================================
//   //
//   // Parent can provide the handler.
//   //
//   // Current project can keep this as a dummy handler.
//   //
//   // Later:
//   //
//   // onConnect(platform)
//   //        ↓
//   // social OAuth service
//   //        ↓
//   // backend
//   //        ↓
//   // Meta / LinkedIn / YouTube etc.
//   //
//   // ============================================================

//   const handleConnect = (platform) => {
//     if (isCreateMode) {
//       return;
//     }

//     if (!organizationId) {
//       return;
//     }

//     if (connectedPlatforms.has(platform)) {
//       return;
//     }

//     if (typeof onConnect !== "function") {
//       return;
//     }

//     onConnect(platform, organizationId);
//   };

//   // ============================================================
//   // RECONNECT HANDLER
//   // ============================================================

//   const handleReconnect = (account) => {
//     if (typeof onReconnect !== "function") {
//       return;
//     }

//     onReconnect(account);
//   };

//   // ============================================================
//   // DISCONNECT HANDLER
//   // ============================================================

//   const handleDisconnect = (account) => {
//     if (typeof onDisconnect !== "function") {
//       return;
//     }

//     onDisconnect(account);
//   };

//   // ============================================================
//   // RENDER
//   // ============================================================

//   return (
//     <Box
//       sx={{
//         width: "100%",
//         mt: 4,
//       }}
//     >
//       {/* ======================================================
//           HEADER
//       ====================================================== */}

//       <Typography
//         sx={{
//           fontSize: 18,
//           fontWeight: 700,
//           color: "#1E293B",
//         }}
//       >
//         Social Accounts
//       </Typography>

//       <Typography
//         sx={{
//           mt: 0.5,
//           mb: 3,
//           fontSize: 15,
//           lineHeight: 1.6,
//           color: "#64748B",
//         }}
//       >
//         Connect and manage the organization's social media
//         accounts.
//       </Typography>

//       {/* ======================================================
//           ERROR
//       ====================================================== */}

//       {error && (
//         <Alert
//           severity="error"
//           sx={{
//             mb: 3,
//             borderRadius: "12px",
//           }}
//         >
//           {error}
//         </Alert>
//       )}

//       {/* ======================================================
//           CONNECTED ACCOUNTS
//       ====================================================== */}

//       <ConnectedAccountsList
//         accounts={accounts}
//         loading={loading}
//         error={error}
//         onReconnect={handleReconnect}
//         onDisconnect={handleDisconnect}
//         actionLoadingId={actionLoadingId}
//       />

//       {/* ======================================================
//           AVAILABLE PLATFORMS
//       ====================================================== */}

//       <Typography
//         sx={{
//           mt: 4,
//           mb: 2,
//           fontSize: 15,
//           fontWeight: 600,
//           color: "#475569",
//         }}
//       >
//         Connect a new account
//       </Typography>

//       {/* ======================================================
//           PLATFORM GRID
//       ====================================================== */}

//       <Box
//         sx={{
//           display: "flex",

//           flexWrap: "wrap",

//           gap: 2,

//           width: "100%",
//         }}
//       >
//         {SOCIAL_PLATFORMS.map((platform) => {
//           const isConnected = connectedPlatforms.has(
//             platform.id,
//           );

//           return (
//             <ConnectSocialAccountCard
//               key={platform.id}
//               platform={platform.id}
//               name={platform.name}
//               backgroundColor={platform.backgroundColor}
//               iconColor={platform.iconColor}
//               connected={isConnected}
//               disabled={isCreateMode}
//               onConnect={handleConnect}
//             />
//           );
//         })}
//       </Box>

//       {/* ======================================================
//           CREATE MODE INFORMATION
//       ====================================================== */}

//       {isCreateMode && (
//         <Box
//           sx={{
//             mt: 2.5,

//             px: 2,

//             py: 1.5,

//             borderRadius: "12px",

//             bgcolor: "#F8FAFC",

//             border: "1px solid #E2E8F0",
//           }}
//         >
//           <Typography
//             sx={{
//               fontSize: 13,
//               color: "#64748B",
//               lineHeight: 1.5,
//             }}
//           >
//             Social accounts can be connected after the
//             organization has been created.
//           </Typography>
//         </Box>
//       )}

//       {/* ======================================================
//           DIVIDER
//       ====================================================== */}

//       <Divider
//         sx={{
//           my: 4,
//         }}
//       />
//     </Box>
//   );
// }

import { Box, Divider, Typography } from "@mui/material";

import { SOCIAL_PLATFORMS } from "../../../constants/social/socialPlatforms";

import ConnectedAccountsList from "./ConnectedAccountsList";
import ConnectSocialAccountCard from "./ConnectSocialAccountCard";

import useSocialAccounts from "../../../hooks/social/useSocialAccounts";

// ============================================================
// SOCIAL ACCOUNTS SECTION
// ============================================================
//
// Single reusable Social Accounts UI.
//
// Used by:
//
// 1. Create Organization
// 2. Edit Organization
// 3. Organization Overview
//
// IMPORTANT:
//
// This component owns the UI composition only.
//
// It does NOT contain:
// - OAuth implementation
// - platform-specific API calls
// - hardcoded account data
// - organization API logic
//
// Platform configuration comes from:
//
// constants/social/socialPlatforms.js
//
// Account data can come from:
//
// 1. parent props
// 2. useSocialAccounts hook
//
// This keeps the UI backend-ready while allowing dummy data
// during the current frontend development stage.
//
// NOTE: error display lives inside ConnectedAccountsList only.
// Don't also render a top-level <Alert> here for the same
// `error` value — that used to double up the error message on
// screen (banner + the list's own error block).
// ============================================================

export default function SocialAccountsSection({
  organizationId = null,

  mode = "overview",

  accounts: providedAccounts = null,

  loading: providedLoading = false,

  error: providedError = null,

  onConnect,

  onReconnect,

  onDisconnect,

  onRetry,

  actionLoadingId = null,
}) {
  // ============================================================
  // DETERMINE DATA SOURCE
  // ============================================================
  //
  // If parent provides accounts:
  //
  //     use provided accounts
  //
  // Otherwise, when an organization ID exists:
  //
  //     useSocialAccounts()
  //
  // This allows dummy data now and backend data later.
  // ============================================================

  const shouldFetchAccounts =
    providedAccounts === null && Boolean(organizationId);

  const {
    accounts: fetchedAccounts,
    loading: fetchedLoading,
    error: fetchedError,
    refetch: refetchAccounts,
  } = useSocialAccounts(organizationId, {
    enabled: shouldFetchAccounts,
  });

  // ============================================================
  // RESOLVE ACCOUNTS
  // ============================================================

  const accounts =
    providedAccounts !== null
      ? Array.isArray(providedAccounts)
        ? providedAccounts
        : []
      : fetchedAccounts;

  // ============================================================
  // RESOLVE LOADING
  // ============================================================

  const loading =
    providedAccounts !== null
      ? Boolean(providedLoading)
      : fetchedLoading;

  // ============================================================
  // RESOLVE ERROR
  // ============================================================

  const error =
    providedAccounts !== null
      ? providedError
      : fetchedError;

  // ============================================================
  // RETRY HANDLER
  // ============================================================
  // Prefers a parent-provided onRetry; falls back to the hook's
  // own refetch when this section is managing its own data.

  const handleRetry = () => {
    if (typeof onRetry === "function") {
      onRetry();
      return;
    }

    if (typeof refetchAccounts === "function") {
      refetchAccounts();
    }
  };

  // ============================================================
  // CONNECTED PLATFORMS
  // ============================================================

  const connectedPlatforms = new Set(
    accounts
      .filter(
        (account) =>
          account?.connected === true ||
          account?.status === "connected",
      )
      .map((account) => account?.platform)
      .filter(Boolean),
  );

  // ============================================================
  // CREATE MODE
  // ============================================================
  //
  // Organization does not exist yet.
  //
  // Therefore OAuth connection cannot actually start yet.
  //
  // But we still render the available platform UI so the user
  // understands that social accounts are part of the setup.
  // ============================================================

  const isCreateMode = mode === "create";

  // ============================================================
  // CONNECT HANDLER
  // ============================================================
  //
  // Parent can provide the handler.
  //
  // Current project can keep this as a dummy handler.
  //
  // Later:
  //
  // onConnect(platform)
  //        ↓
  // social OAuth service
  //        ↓
  // backend
  //        ↓
  // Meta / LinkedIn / YouTube etc.
  //
  // ============================================================

  const handleConnect = (platform) => {
    if (isCreateMode) {
      return;
    }

    if (!organizationId) {
      return;
    }

    if (connectedPlatforms.has(platform)) {
      return;
    }

    if (typeof onConnect !== "function") {
      return;
    }

    onConnect(platform, organizationId);
  };

  // ============================================================
  // RECONNECT HANDLER
  // ============================================================

  const handleReconnect = (account) => {
    if (typeof onReconnect !== "function") {
      return;
    }

    onReconnect(account);
  };

  // ============================================================
  // DISCONNECT HANDLER
  // ============================================================

  const handleDisconnect = (account) => {
    if (typeof onDisconnect !== "function") {
      return;
    }

    onDisconnect(account);
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <Box
      sx={{
        width: "100%",
        mt: 4,
      }}
    >
      {/* ======================================================
          HEADER
      ====================================================== */}

      <Typography
        component="h2"
        sx={{
          fontSize: 18,
          fontWeight: 700,
          color: "#1E293B",
          m: 0,
        }}
      >
        Social accounts
      </Typography>

      <Typography
        sx={{
          mt: 0.5,
          mb: 3,
          fontSize: 15,
          lineHeight: 1.6,
          color: "#64748B",
        }}
      >
        Connect and manage the organization's social media
        accounts.
      </Typography>

      {/* ======================================================
          CONNECTED ACCOUNTS
          (error, loading and empty states are all handled
          inside ConnectedAccountsList — don't duplicate them
          here with a second <Alert>)
      ====================================================== */}

      <ConnectedAccountsList
        accounts={accounts}
        loading={loading}
        error={error}
        onReconnect={handleReconnect}
        onDisconnect={handleDisconnect}
        onRetry={handleRetry}
        actionLoadingId={actionLoadingId}
      />

      {/* ======================================================
          AVAILABLE PLATFORMS
      ====================================================== */}

      <Typography
        component="h3"
        sx={{
          mt: 4,
          mb: 2,
          fontSize: 15,
          fontWeight: 600,
          color: "#475569",
        }}
      >
        Connect a new account
      </Typography>

      {/* ======================================================
          PLATFORM GRID
      ====================================================== */}

      <Box
        sx={{
          display: "flex",

          flexWrap: "wrap",

          gap: 2,

          width: "100%",
        }}
      >
        {SOCIAL_PLATFORMS.map((platform) => {
          const isConnected = connectedPlatforms.has(
            platform.id,
          );

          return (
            <ConnectSocialAccountCard
              key={platform.id}
              platform={platform.id}
              name={platform.name}
              backgroundColor={platform.backgroundColor}
              iconColor={platform.iconColor}
              connected={isConnected}
              disabled={isCreateMode}
              onConnect={handleConnect}
            />
          );
        })}
      </Box>

      {/* ======================================================
          CREATE MODE INFORMATION
      ====================================================== */}

      {isCreateMode && (
        <Box
          role="note"
          sx={{
            mt: 2.5,

            px: 2,

            py: 1.5,

            borderRadius: "12px",

            bgcolor: "#F8FAFC",

            border: "1px solid #E2E8F0",
          }}
        >
          <Typography
            sx={{
              fontSize: 13,
              color: "#64748B",
              lineHeight: 1.5,
            }}
          >
            Social accounts can be connected after the
            organization has been created.
          </Typography>
        </Box>
      )}

      {/* ======================================================
          DIVIDER
      ====================================================== */}

      <Divider
        sx={{
          my: 4,
        }}
      />
    </Box>
  );
}