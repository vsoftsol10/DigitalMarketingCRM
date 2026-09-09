import { Box, Divider, Typography } from "@mui/material";

import { useEffect } from "react";

import { SOCIAL_PLATFORMS } from "../../../constants/social/socialPlatforms";

import ConnectedAccountsList from "./ConnectedAccountsList";

import ConnectSocialAccountCard from "./ConnectSocialAccountCard";

import useSocialAccounts from "../../../hooks/social/useSocialAccounts";

// ============================================================
// SOCIAL ACCOUNTS SECTION
// ============================================================
//
// Responsibilities:
//
// - Render connected social accounts
// - Render social platform cards
// - Delegate OAuth actions to parent
// - Refresh connected accounts when parent requests refresh
//
// This component does NOT:
//
// - Implement OAuth
// - Call Meta API directly
// - Select Facebook Pages
// - Select Instagram accounts
// - Store Meta tokens
//
// ============================================================

export default function SocialAccountsSection({
  organizationId,

  mode = "overview",

  // ==========================================================
  // OPTIONAL CONTROLLED ACCOUNT DATA
  // ==========================================================

  accounts: providedAccounts = null,

  loading: providedLoading = false,

  error: providedError = null,

  // ==========================================================
  // ACTION HANDLERS
  // ==========================================================

  onConnect,

  onReconnect,

  onDisconnect,

  onRetry,

  // ==========================================================
  // LOADING STATES
  // ==========================================================

  actionLoadingId = null,

  connectingPlatform = null,

  // ==========================================================
  // EXTERNAL REFRESH
  // ==========================================================
  //
  // Parent increments this value after OAuth callback success.
  //
  // ==========================================================

  refreshKey = 0,
}) {
  // ============================================================
  // CREATE MODE
  // ============================================================

  const isCreateMode = mode === "create";

  // ============================================================
  // ACCOUNT DATA SOURCE
  // ============================================================
  //
  // Parent provides accounts:
  //     use parent data
  //
  // Parent does not provide accounts:
  //     use backend hook
  //
  // null means parent did not provide account data.
  //
  // ============================================================

  const shouldFetchAccounts =
    providedAccounts === null && Boolean(organizationId) && !isCreateMode;

  const {
    accounts: fetchedAccounts,
    loading: fetchedLoading,
    error: fetchedError,
    refresh: refreshAccounts,
  } = useSocialAccounts(organizationId, {
    enabled: shouldFetchAccounts,
  });

  // ============================================================
  // REFRESH AFTER OAUTH CALLBACK
  // ============================================================

  useEffect(() => {
    if (!shouldFetchAccounts) {
      return;
    }

    if (typeof refreshAccounts !== "function") {
      return;
    }

    refreshAccounts();
  }, [refreshKey, shouldFetchAccounts, refreshAccounts]);

  // ============================================================
  // RESOLVE ACCOUNTS
  // ============================================================

  const resolvedAccounts =
    providedAccounts !== null
      ? Array.isArray(providedAccounts)
        ? providedAccounts
        : []
      : fetchedAccounts;

  // ============================================================
  // RESOLVE LOADING
  // ============================================================

  const resolvedLoading =
    providedAccounts !== null
      ? Boolean(providedLoading)
      : Boolean(fetchedLoading);

  // ============================================================
  // RESOLVE ERROR
  // ============================================================

  const resolvedError =
    providedAccounts !== null ? providedError : fetchedError;

  // ============================================================
  // RETRY
  // ============================================================

  const handleRetry = () => {
    if (typeof onRetry === "function") {
      onRetry();

      return;
    }

    if (typeof refreshAccounts === "function") {
      refreshAccounts();
    }
  };

  // ============================================================
  // CONNECT
  // ============================================================

  const handleConnect = (platform) => {
    if (isCreateMode) {
      return;
    }

    if (!organizationId) {
      return;
    }

    if (typeof onConnect !== "function") {
      return;
    }

    // IMPORTANT:
    //
    // Pass only the platform ID.
    //
    // Example:
    //
    // "meta"
    //
    // NOT:
    //
    // {
    //   id: "meta",
    //   name: "Meta",
    //   ...
    // }
    //
    onConnect(platform.id, organizationId);
  };

  // ============================================================
  // RECONNECT
  // ============================================================

  const handleReconnect = (account) => {
    if (typeof onReconnect !== "function") {
      return;
    }

    onReconnect(account);
  };

  // ============================================================
  // DISCONNECT
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
        Connect and manage the organization's social media accounts.
      </Typography>

      {/* ======================================================
          CONNECTED ACCOUNTS
      ====================================================== */}

      <ConnectedAccountsList
        accounts={resolvedAccounts}
        loading={resolvedLoading}
        error={resolvedError}
        onReconnect={handleReconnect}
        onDisconnect={handleDisconnect}
        onRetry={handleRetry}
        actionLoadingId={actionLoadingId}
      />

      {/* ======================================================
          CONNECT NEW ACCOUNT
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
        {SOCIAL_PLATFORMS.map((platform) => (
          <ConnectSocialAccountCard
            key={platform.id}
            platform={platform}
            onConnect={handleConnect}
            loading={connectingPlatform === platform.id}
          />
        ))}
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
            Social accounts can be connected after the organization has been
            created.
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
