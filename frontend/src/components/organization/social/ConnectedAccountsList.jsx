import { Box, Button, Typography } from "@mui/material";

import ConnectedAccountRow from "./ConnectedAccountRow";
import SocialAccountEmptyState from "./SocialAccountEmptyState";

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

  // ============================================================
  // LOADING STATE
  // ============================================================

  if (loading) {
    return (
      <Box
        role="status"
        aria-live="polite"
        sx={{
          py: 5,
          textAlign: "center",
        }}
      >
        <Typography
          sx={{
            fontSize: 14,
            fontWeight: 500,
            color: "#64748B",
          }}
        >
          Loading connected accounts...
        </Typography>
      </Box>
    );
  }

  // ============================================================
  // ERROR STATE
  // ============================================================

  if (error) {
    return (
      <Box
        role="alert"
        sx={{
          py: 4,
          px: 3,

          border: "1px solid #FECACA",

          borderRadius: "16px",

          bgcolor: "#FEF2F2",

          textAlign: "center",
        }}
      >
        <Typography
          sx={{
            fontSize: 14,
            fontWeight: 600,
            color: "#B91C1C",
          }}
        >
          Unable to load social accounts
        </Typography>

        <Typography
          sx={{
            mt: 0.5,
            fontSize: 13,
            color: "#DC2626",
          }}
        >
          {error}
        </Typography>

        {typeof onRetry === "function" && (
          <Button
            type="button"
            variant="outlined"
            size="small"
            onClick={onRetry}
            sx={{
              mt: 2,
              height: 34,
              borderRadius: "10px",
              borderColor: "#FECACA",
              color: "#B91C1C",
              textTransform: "none",
              fontSize: 13,
              fontWeight: 600,
              "&:hover": {
                borderColor: "#DC2626",
                bgcolor: "#FEF2F2",
              },
            }}
          >
            Try again
          </Button>
        )}
      </Box>
    );
  }

  // ============================================================
  // EMPTY STATE
  // ============================================================

  if (normalizedAccounts.length === 0) {
    return <SocialAccountEmptyState />;
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
