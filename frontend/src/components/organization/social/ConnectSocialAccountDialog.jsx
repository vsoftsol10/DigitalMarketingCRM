import React from "react";
import PropTypes from "prop-types";

import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Typography,
} from "@mui/material";

// ============================================================
// PLATFORM CONFIGURATION
// ============================================================

const PLATFORM_CONFIG = {
  facebook: {
    connect: {
      title: "Connect Facebook",
      continueLabel: "Continue with Facebook",
      loadingLabel: "Connecting...",
      message: "Your Facebook login will open in the next step.",

      requirements: [
        {
          title: "Facebook account",
          description:
            "Make sure you can sign in to the Facebook account you want to use.",
        },
        {
          title: "Facebook Page",
          description:
            "Make sure the Facebook Page you want to connect is already connected to a Business Portfolio.",
        },
        {
          title: "Page access",
          description:
            "Make sure you have the required access to manage the Facebook Page.",
        },
      ],
    },

    reconnect: {
      title: "Reconnect Facebook",
      continueLabel: "Continue with Facebook",
      loadingLabel: "Reconnecting...",
      message:
        "Your Facebook login will open in the next step. Make sure you are using the same Meta Business Portfolio that was previously used to connect this Page.",

      requirements: [
        {
          title: "Same Meta Business Portfolio",
          description:
            "Make sure you are logged in to the same Meta Business Portfolio that was previously used to connect this Facebook Page.",
        },
        {
          title: "Facebook Page",
          description:
            "Make sure the Facebook Page you want to reconnect is available in that Business Portfolio.",
        },
        {
          title: "Page access",
          description:
            "Make sure you have the required access to manage the Facebook Page.",
        },
      ],
    },
  },

  instagram: {
    connect: {
      title: "Connect Instagram",
      continueLabel: "Continue with Instagram",
      loadingLabel: "Connecting...",
      message: "Your Instagram login will open in the next step.",

      requirements: [
        {
          title: "Professional Instagram account",
          description:
            "Make sure the Instagram account you want to connect is a Professional account.",
        },
        {
          title: "Instagram access",
          description:
            "Make sure you can sign in to the Instagram account you want to connect.",
        },
        {
          title: "Authorization",
          description:
            "You'll need to authorize access to connect your Instagram account.",
        },
      ],
    },

    reconnect: {
      title: "Reconnect Instagram",
      continueLabel: "Continue with Instagram",
      loadingLabel: "Reconnecting...",
      message:
        "Your Instagram login will open in the next step. Make sure you are logged in to the same Instagram account that was previously connected.",

      requirements: [
        {
          title: "Same Instagram account",
          description:
            "Make sure you are logged in to the same Instagram account that was previously connected.",
        },
        {
          title: "Professional Instagram account",
          description:
            "Make sure the Instagram account is still a Professional account.",
        },
        {
          title: "Authorization",
          description:
            "You'll need to authorize access again to reconnect your Instagram account.",
        },
      ],
    },
  },
};

// ============================================================
// COMPONENT
// ============================================================

const ConnectSocialAccountDialog = ({
  isOpen,
  platform,
  mode = "connect",
  onClose,
  onContinue,
  isLoading = false,
}) => {
  // ==========================================================
  // PLATFORM CONFIG
  // ==========================================================

  const platformConfig = PLATFORM_CONFIG[platform];

  const config = platformConfig?.[mode];

  // ==========================================================
  // INVALID / CLOSED STATE
  // ==========================================================

  if (!config) {
    return null;
  }

  // ==========================================================
  // CONTINUE
  // ==========================================================

  const handleContinue = () => {
    if (isLoading) {
      return;
    }

    onContinue(platform);
  };

  // ==========================================================
  // CLOSE
  // ==========================================================

  const handleClose = () => {
    if (isLoading) {
      return;
    }

    onClose();
  };

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <Dialog
      open={isOpen}
      onClose={handleClose}
      fullWidth
      maxWidth="sm"
      aria-labelledby="social-account-dialog-title"
      aria-describedby="social-account-dialog-description"
    >
      {/* ======================================================
          TITLE
      ====================================================== */}

      <DialogTitle
        id="social-account-dialog-title"
        sx={{
          px: 3,
          pt: 3,
          pb: 1,
          fontSize: "1.25rem",
          fontWeight: 600,
          color: "#111827",
        }}
      >
        {config.title}
      </DialogTitle>

      {/* ======================================================
          CONTENT
      ====================================================== */}

      <DialogContent
        id="social-account-dialog-description"
        sx={{
          px: 3,
          py: 2,
        }}
      >
        {/* ====================================================
            INTRO
        ==================================================== */}

        <Typography
          variant="body2"
          sx={{
            mb: 2.5,
            color: "#6B7280",
            fontSize: "0.875rem",
          }}
        >
          Before you continue
        </Typography>

        {/* ====================================================
            REQUIREMENTS
        ==================================================== */}

        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 2.5,
          }}
        >
          {config.requirements.map((requirement, index) => (
            <Box
              key={requirement.title}
              sx={{
                display: "flex",
                alignItems: "flex-start",
                gap: 1.5,
              }}
            >
              {/* ==================================================
                  NUMBER
              ================================================== */}

              <Box
                sx={{
                  width: 28,
                  height: 28,
                  minWidth: 28,
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  backgroundColor: "#F3F4F6",
                  color: "#374151",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                }}
              >
                {index + 1}
              </Box>

              {/* ==================================================
                  REQUIREMENT CONTENT
              ================================================== */}

              <Box
                sx={{
                  minWidth: 0,
                  flex: 1,
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    fontSize: "0.875rem",
                    fontWeight: 600,
                    lineHeight: 1.5,
                    color: "#111827",
                  }}
                >
                  {requirement.title}
                </Typography>

                <Typography
                  variant="body2"
                  sx={{
                    mt: 0.5,
                    fontSize: "0.8125rem",
                    lineHeight: 1.6,
                    color: "#6B7280",
                  }}
                >
                  {requirement.description}
                </Typography>
              </Box>
            </Box>
          ))}
        </Box>

        {/* ====================================================
            INFORMATION MESSAGE
        ==================================================== */}

        <Box
          sx={{
            mt: 3,
            px: 2,
            py: 1.5,
            borderRadius: "10px",
            backgroundColor: mode === "reconnect" ? "#FFFBEB" : "#F9FAFB",
            border:
              mode === "reconnect" ? "1px solid #FDE68A" : "1px solid #E5E7EB",
          }}
        >
          <Typography
            variant="body2"
            sx={{
              fontSize: "0.8125rem",
              lineHeight: 1.6,
              color: mode === "reconnect" ? "#92400E" : "#4B5563",
            }}
          >
            {config.message}
          </Typography>
        </Box>
      </DialogContent>

      {/* ======================================================
          ACTIONS
      ====================================================== */}

      <Divider />

      <DialogActions
        sx={{
          px: 3,
          py: 2,
          gap: 1,
        }}
      >
        {/* ====================================================
            CANCEL
        ==================================================== */}

        <Button
          type="button"
          variant="outlined"
          onClick={handleClose}
          disabled={isLoading}
          sx={{
            minWidth: 90,
            textTransform: "none",
            borderRadius: "8px",
            borderColor: "#D1D5DB",
            color: "#374151",

            "&:hover": {
              borderColor: "#9CA3AF",
              backgroundColor: "#F9FAFB",
            },
          }}
        >
          Cancel
        </Button>

        {/* ====================================================
            CONTINUE
        ==================================================== */}

        <Button
          type="button"
          variant="contained"
          onClick={handleContinue}
          disabled={isLoading}
          sx={{
            minWidth: 180,
            textTransform: "none",
            borderRadius: "8px",
            backgroundColor: "#111827",

            "&:hover": {
              backgroundColor: "#1F2937",
            },

            "&.Mui-disabled": {
              backgroundColor: "#D1D5DB",
              color: "#6B7280",
            },
          }}
        >
          {isLoading ? config.loadingLabel : config.continueLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// ============================================================
// PROP TYPES
// ============================================================

ConnectSocialAccountDialog.propTypes = {
  isOpen: PropTypes.bool.isRequired,

  platform: PropTypes.oneOf(["facebook", "instagram"]),

  mode: PropTypes.oneOf(["connect", "reconnect"]),

  onClose: PropTypes.func.isRequired,

  onContinue: PropTypes.func.isRequired,

  isLoading: PropTypes.bool,
};

// ============================================================
// DEFAULT PROPS
// ============================================================

ConnectSocialAccountDialog.defaultProps = {
  platform: null,
  mode: "connect",
  isLoading: false,
};

// ============================================================
// EXPORT
// ============================================================

export default ConnectSocialAccountDialog;
