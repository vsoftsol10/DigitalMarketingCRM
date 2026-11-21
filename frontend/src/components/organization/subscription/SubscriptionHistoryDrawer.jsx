import {
  Alert,
  Box,
  Button,
  Drawer,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";

import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";

import SubscriptionHistoryItem from "./SubscriptionHistoryItem";
import LoadingState from "../../ui/LoadingState";
import ErrorState from "../../ui/ErrorState";
import EmptyState from "../../ui/EmptyState";

const DRAWER_WIDTH = 460;

export default function SubscriptionHistoryDrawer({
  open,
  onClose,
  subscriptions = [],
  hasLoadedHistory = false,
  loading = false,
  error = null,
  onRetry,
}) {
  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      ModalProps={{
        keepMounted: true,
      }}
      PaperProps={{
        sx: {
          width: {
            xs: "100%",
            sm: DRAWER_WIDTH,
          },

          maxWidth: "100vw",

          height: "100vh",

          borderRadius: 0,

          borderLeft: "1px solid #DDE3F1",
          background: "#FFFFFF",
          boxShadow: "-8px 0 24px rgba(31,41,80,.1)",

          display: "flex",
          flexDirection: "column",
        },
      }}
    >
      {/* =====================================================
          HEADER
      ===================================================== */}

      <Box
        sx={{
          px: 3,
          py: 2.5,

          borderBottom: "1px solid #E5E9F1",
          background: "#FFFFFF",
          boxShadow: "none",

          flexShrink: 0,

          position: "sticky",
          top: 0,
          zIndex: 2,
        }}
      >
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          spacing={2}
        >
          <Stack
            direction="row"
            alignItems="center"
            spacing={1.5}
            sx={{
              minWidth: 0,
            }}
          >
            <Box
              sx={{
                width: 40,
                height: 40,

                borderRadius: "11px",

                background: "#F1F5F9",
                color: "#64748B",
                border: "1px solid #E5E9F1",
                boxShadow: "none",

                display: "flex",
                alignItems: "center",
                justifyContent: "center",

                flexShrink: 0,
              }}
            >
              <HistoryOutlinedIcon
                sx={{
                  fontSize: 20,
                }}
              />
            </Box>

            <Box
              sx={{
                minWidth: 0,
              }}
            >
              <Typography
                sx={{
                  fontSize: 17,
                  lineHeight: "23px",
                  fontWeight: 700,

                  color: "#17294F",
                }}
              >
                Subscription History
              </Typography>

              <Typography
                sx={{
                  mt: 0.25,

                  fontSize: 13,
                  lineHeight: "18px",

                  color: "#657899",
                }}
              >
                Complete subscription timeline
              </Typography>
            </Box>
          </Stack>

          <IconButton
            onClick={onClose}
            aria-label="Close subscription history"
            sx={{
              width: 40,
              height: 40,

              color: "#64748B",

              borderRadius: "12px",

              border: "1px solid #E1E5F0",
              boxShadow: "none",

              "&:hover": {
                background: "#F8FAFC",
                color: "#172554",
              },
            }}
          >
            <CloseRoundedIcon />
          </IconButton>
        </Stack>
      </Box>

      {/* =====================================================
          CONTENT
      ===================================================== */}

      <Box
        sx={{
          flex: 1,

          overflowY: "auto",

          px: 3,
          py: 3,

          "&::-webkit-scrollbar": {
            width: 7,
          },

          "&::-webkit-scrollbar-track": {
            background: "transparent",
          },

          "&::-webkit-scrollbar-thumb": {
            backgroundColor: "rgba(133,154,193,.48)",
            borderRadius: 10,
          },

          "&::-webkit-scrollbar-thumb:hover": {
            backgroundColor: "rgba(105,128,171,.62)",
          },
        }}
      >
        {/* ===================================================
            LOADING
        =================================================== */}

        {loading && !hasLoadedHistory && (
          <LoadingState
            label="LOADING SUBSCRIPTION HISTORY..."
            variant="container"
            minHeight={320}
          />
        )}

        {loading && hasLoadedHistory && (
          <LoadingState
            label="REFRESHING SUBSCRIPTION HISTORY..."
            variant="inline"
          />
        )}

        {/* ===================================================
            ERROR
        =================================================== */}

        {!loading && error && !hasLoadedHistory && (
          <ErrorState
            title="Unable to load subscription history"
            message={error}
            onRetry={onRetry ? () => { void onRetry(); } : undefined}
            retryLabel="Retry"
            variant="inline"
            sx={{ minHeight: 320 }}
          />
        )}

        {error && hasLoadedHistory && (
          <Alert
            severity="error"
            sx={{
              borderRadius: "12px",
            }}
            action={onRetry ? (
              <Button
                color="inherit"
                size="small"
                disabled={loading}
                onClick={() => { void onRetry(); }}
              >
                Retry
              </Button>
            ) : undefined}
          >
            Could not refresh subscription history. Previously loaded history remains available. {error}
          </Alert>
        )}

        {/* ===================================================
            EMPTY
        =================================================== */}

        {hasLoadedHistory && !loading && !error && subscriptions.length === 0 && (
          <EmptyState
            icon={<HistoryOutlinedIcon />}
            title="No subscription history"
            description="Subscription activity will appear here once a subscription is created."
            sx={{ minHeight: 320 }}
          />
        )}

        {/* ===================================================
            HISTORY LIST
        =================================================== */}

        {hasLoadedHistory && subscriptions.length > 0 && (
          <Box>
            {subscriptions.map((subscription, index) => (
              <SubscriptionHistoryItem
                key={subscription.id}
                subscription={subscription}
                isLast={index === subscriptions.length - 1}
              />
            ))}
          </Box>
        )}
      </Box>
    </Drawer>
  );
}
