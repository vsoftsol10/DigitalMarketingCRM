import { Box, Divider, Typography } from "@mui/material";

import { useEffect, useRef } from "react";

import { SOCIAL_PLATFORMS } from "../../../constants/social/socialPlatforms";

import ConnectedAccountsList from "./ConnectedAccountsList";

import ConnectSocialAccountCard from "./ConnectSocialAccountCard";
import overviewGlassCardSx from "../overview/overviewGlassCardSx";

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

  refreshKey = 0,
}) {
  // ============================================================
  // CREATE MODE
  // ============================================================

  const isCreateMode = mode === "create";

  // ============================================================
  // ACCOUNT DATA SOURCE
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

  const previousRefreshKey = useRef(refreshKey);

  // ============================================================
  // REFRESH AFTER OAUTH CALLBACK
  // ============================================================

  useEffect(() => {
    const refreshKeyChanged = previousRefreshKey.current !== refreshKey;
    previousRefreshKey.current = refreshKey;

    if (!shouldFetchAccounts) {
      return;
    }

    if (!refreshKeyChanged) {
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

    const platformId =
      typeof platform === "string" ? platform : platform?.id || "";

    if (!platformId) {
      return;
    }

    onConnect(platformId, organizationId);
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

  const overviewSectionSx = {
    ...overviewGlassCardSx,
    p: { xs: 2, sm: 2.5 },
  };

  return (
    <Box
      sx={{
        width: "100%",
        mt: isCreateMode ? 4 : 0,
      }}
    >
      <Box
        component="section"
        sx={!isCreateMode ? overviewSectionSx : undefined}
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
          mb: isCreateMode ? 3 : 2.5,
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
      </Box>

      {/* ======================================================
          CONNECT NEW ACCOUNT
      ====================================================== */}

      <Box
        component="section"
        sx={!isCreateMode ? { ...overviewSectionSx, mt: 2.5 } : undefined}
      >
      <Typography
        component="h3"
        sx={{
          mt: isCreateMode ? 4 : 0,
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
          display: isCreateMode ? "flex" : "grid",
          gridTemplateColumns: isCreateMode
            ? undefined
            : {
                xs: "repeat(1, minmax(0, 1fr))",
                sm: "repeat(2, minmax(0, 1fr))",
                lg: "repeat(4, minmax(0, 1fr))",
              },
          flexWrap: isCreateMode ? "wrap" : undefined,
          gap: isCreateMode ? 2 : 1.5,
          width: "100%",
        }}
      >
        {SOCIAL_PLATFORMS.map((platform) => (
          <ConnectSocialAccountCard
            key={platform.id}
            platform={platform}
            onConnect={handleConnect}
            loading={connectingPlatform === platform.id}
            overviewStyle={!isCreateMode}
          />
        ))}
      </Box>
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
            borderRadius: "14px",
            background: "linear-gradient(145deg, rgba(240,246,255,.92), rgba(250,252,255,.94))",
            border: "1px solid rgba(255,255,255,.92)",
            boxShadow: "0 5px 12px rgba(76,98,154,.08), inset 0 1px 0 rgba(255,255,255,.98)",
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

      {isCreateMode && <Divider
        sx={{
          my: 3,
          borderColor: "rgba(146,168,201,.28)",
        }}
      />}
    </Box>
  );
}
