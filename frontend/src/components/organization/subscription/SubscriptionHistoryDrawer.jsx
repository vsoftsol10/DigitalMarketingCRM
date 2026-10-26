import {
  Alert,
  Box,
  Drawer,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";

import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";

import SubscriptionHistoryItem from "./SubscriptionHistoryItem";
import LoadingState from "../../ui/LoadingState";

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

          borderLeft: "1px solid rgba(255,255,255,.9)",

          background:
            "linear-gradient(145deg, rgba(250,252,255,.98) 0%, rgba(242,247,255,.96) 58%, rgba(237,244,255,.92) 100%)",

          boxShadow:
            "-10px 0 30px rgba(75,96,151,.14), -2px 0 8px rgba(79,99,154,.09), inset 1px 0 0 rgba(255,255,255,.78)",

          backdropFilter: "blur(16px)",

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

          borderBottom: "1px solid rgba(146,168,201,.24)",

          background:
            "linear-gradient(145deg, rgba(250,252,255,.98) 0%, rgba(242,247,255,.96) 100%)",

          boxShadow: "inset 0 1px 0 rgba(255,255,255,.98)",

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

                background:
                  "linear-gradient(145deg, rgba(238,245,255,.98), rgba(222,234,252,.95))",

                color: "#4B70C7",

                border: "1px solid rgba(255,255,255,.9)",

                boxShadow:
                  "0 5px 12px rgba(75,96,151,.1), inset 0 2px 0 rgba(255,255,255,.98)",

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

              color: "#657899",

              borderRadius: "12px",

              border: "1px solid rgba(255,255,255,.82)",

              boxShadow:
                "0 4px 10px rgba(75,96,151,.08), inset 0 1px 0 rgba(255,255,255,.98)",

              "&:hover": {
                background: "rgba(231,240,255,.76)",
                color: "#17294F",
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

        {loading && (
          <LoadingState
            label="LOADING SUBSCRIPTION HISTORY..."
            variant="container"
            minHeight={320}
          />
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

                  background:
                    "linear-gradient(145deg, rgba(238,245,255,.98), rgba(222,234,252,.9))",

                  border: "1px solid rgba(255,255,255,.9)",

                  boxShadow:
                    "0 4px 10px rgba(75,96,151,.08), inset 0 1px 0 rgba(255,255,255,.96)",

                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",

                  color: "#7184AD",
                }}
              >
                <HistoryOutlinedIcon />
              </Box>

              <Typography
                sx={{
                  fontSize: 14,
                  fontWeight: 600,
                  color: "#17294F",
                }}
              >
                No subscription history
              </Typography>

              <Typography
                sx={{
                  maxWidth: 280,

                  fontSize: 13,
                  lineHeight: "19px",

                  color: "#657899",
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
