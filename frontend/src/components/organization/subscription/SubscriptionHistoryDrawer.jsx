import {
  Alert,
  Box,
  CircularProgress,
  Drawer,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";

import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";

import SubscriptionHistoryItem from "./SubscriptionHistoryItem";

const DRAWER_WIDTH = 460;

export default function SubscriptionHistoryDrawer({
  open,
  onClose,
  subscriptions = [],
  loading = false,
  error = null,
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

          borderLeft: "1px solid #E2E8F0",

          backgroundColor: "#FFFFFF",

          boxShadow: "-8px 0 32px rgba(15, 23, 42, 0.08)",

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

          borderBottom: "1px solid #E2E8F0",

          backgroundColor: "#FFFFFF",

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

                backgroundColor: "#EEF4FF",

                color: "#2563EB",

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

                  color: "#0F172A",
                }}
              >
                Subscription History
              </Typography>

              <Typography
                sx={{
                  mt: 0.25,

                  fontSize: 13,
                  lineHeight: "18px",

                  color: "#64748B",
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

              borderRadius: "10px",

              "&:hover": {
                backgroundColor: "#F8FAFC",
                color: "#0F172A",
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
            backgroundColor: "#CBD5E1",
            borderRadius: 10,
          },

          "&::-webkit-scrollbar-thumb:hover": {
            backgroundColor: "#94A3B8",
          },
        }}
      >
        {/* ===================================================
            LOADING
        =================================================== */}

        {loading && (
          <Box
            sx={{
              minHeight: 320,

              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Stack spacing={1.5} alignItems="center">
              <CircularProgress size={28} />

              <Typography
                sx={{
                  fontSize: 13,
                  color: "#64748B",
                }}
              >
                Loading subscription history...
              </Typography>
            </Stack>
          </Box>
        )}

        {/* ===================================================
            ERROR
        =================================================== */}

        {!loading && error && (
          <Alert
            severity="error"
            sx={{
              borderRadius: "12px",
            }}
          >
            {error}
          </Alert>
        )}

        {/* ===================================================
            EMPTY
        =================================================== */}

        {!loading && !error && subscriptions.length === 0 && (
          <Box
            sx={{
              minHeight: 320,

              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Stack
              spacing={1}
              alignItems="center"
              sx={{
                textAlign: "center",
              }}
            >
              <Box
                sx={{
                  width: 48,
                  height: 48,

                  borderRadius: "14px",

                  backgroundColor: "#F8FAFC",

                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",

                  color: "#94A3B8",
                }}
              >
                <HistoryOutlinedIcon />
              </Box>

              <Typography
                sx={{
                  fontSize: 14,
                  fontWeight: 600,
                  color: "#334155",
                }}
              >
                No subscription history
              </Typography>

              <Typography
                sx={{
                  maxWidth: 280,

                  fontSize: 13,
                  lineHeight: "19px",

                  color: "#64748B",
                }}
              >
                Subscription activity will appear here once a subscription is
                created.
              </Typography>
            </Stack>
          </Box>
        )}

        {/* ===================================================
            HISTORY LIST
        =================================================== */}

        {!loading && !error && subscriptions.length > 0 && (
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
