import { Alert, AlertTitle, Box } from "@mui/material";
import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";

import ConnectedAccountRow from "./ConnectedAccountRow";
import LoadingState from "../../ui/LoadingState";
import ErrorState from "../../ui/ErrorState";
import EmptyState from "../../ui/EmptyState";
import { getParentReconnectGroups } from "./reconnectStatus";

// ============================================================
// CONNECTED ACCOUNTS LIST
// ============================================================
//
// Reusable presentation component.
//
// This component:
// - Does NOT call the backend
// - Does NOT know about API endpoints
// - Does NOT contain OAuth logic
// - Only renders the accounts received through props
//
// This makes it reusable for:
//
// Create Organization
// Edit Organization
// Organization Overview
//
// Later when backend is connected:
//
// API
//   ↓
// Hook / Container
//   ↓
// ConnectedAccountsList
//   ↓
// ConnectedAccountRow
//
// ============================================================

export default function ConnectedAccountsList({
  accounts = [],
  loading = false,
  error = null,
  onReconnect,
  onDisconnect,
  onRetry,
  actionLoadingId = null,
}) {
  // ============================================================
  // NORMALIZE ACCOUNTS
  // ============================================================
  // Filter out falsy entries, then build a guaranteed-unique key
  // for each row. account.id is preferred; platform+username is
  // the fallback, but two accounts on the same platform with no
  // username (or both missing username) would collide, so the
  // array index is folded in as a last-resort tiebreaker.

  const normalizedAccounts = (Array.isArray(accounts) ? accounts : [])
    .filter(Boolean)
    .map((account, index) => ({
      ...account,
      _rowKey:
        account.id != null
          ? String(account.id)
          : `${account.platform || "account"}-${account.username || "unknown"}-${index}`,
    }));

  const parentReconnectGroups = getParentReconnectGroups(normalizedAccounts);

  // ============================================================
  // LOADING STATE
  // ============================================================

  if (loading && normalizedAccounts.length === 0) {
    return (
      <LoadingState
        label="LOADING CONNECTED ACCOUNTS..."
        variant="container"
        minHeight={120}
      />
    );
  }

  // ============================================================
  // ERROR STATE
  // ============================================================

  if (error && normalizedAccounts.length === 0) {
    return (
      <ErrorState
        title="Unable to load social accounts"
        message={error}
        onRetry={loading ? undefined : onRetry}
        variant="container"
      />
    );
  }

  // ============================================================
  // EMPTY STATE
  // ============================================================

  if (normalizedAccounts.length === 0) {
    return (
      <EmptyState
        icon={<ShareOutlinedIcon />}
        title="No accounts connected yet"
        description="Connect this organization's social accounts to start publishing and managing social activity."
        sx={{ minHeight: 190 }}
      />
    );
  }

  // ============================================================
  // ACCOUNT LIST
  // ============================================================

  return (
    <Box
      sx={{
        width: "100%",
      }}
    >
      {error && (
        <ErrorState
          title="Unable to refresh social accounts"
          message={error}
          onRetry={loading ? undefined : onRetry}
          variant="inline"
        />
      )}

      {loading && (
        <LoadingState label="UPDATING CONNECTED ACCOUNTS..." variant="inline" />
      )}

      {parentReconnectGroups.map((group) => {
        const pageNames = group.accounts
          .map((account) => account.pageName || account.accountName)
          .filter(Boolean);
        const connectedActivePageExists = group.accounts.some(
          (account) => (
            account.connected === true
            && account.valid === true
            && account.credentialStatus === "active"
          ),
        );

        return (
          <Alert
            key={group.key}
            severity="warning"
            sx={{ mt: 2, alignItems: "flex-start" }}
          >
            <AlertTitle>Meta connection needs reconnect</AlertTitle>
            The parent Facebook USER authorization{pageNames.length > 0
              ? ` shared by ${pageNames.join(", ")}`
              : " for these Pages"} needs reconnect
            {group.parentUserCredentialStatus
              ? ` (status: ${group.parentUserCredentialStatus}). `
              : ". "}
            {connectedActivePageExists && (
              <> Connected Pages with an active Page credential remain available for Page-level publishing and Insights.</>
            )}
          </Alert>
        );
      })}

      {normalizedAccounts.map((account) => (
        <ConnectedAccountRow
          key={account._rowKey}
          account={account}
          onReconnect={onReconnect}
          onDisconnect={onDisconnect}
          loading={actionLoadingId === account.id}
        />
      ))}
    </Box>
  );
}
