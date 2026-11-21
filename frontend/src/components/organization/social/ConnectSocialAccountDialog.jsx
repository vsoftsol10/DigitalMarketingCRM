import PropTypes from "prop-types";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import InstagramIcon from "@mui/icons-material/Instagram";

import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";
import {
  socialDialogActionsSx,
  socialDialogFacebookIconTileSx,
  socialDialogInfoSx,
  socialDialogInstagramIconTileSx,
  socialDialogNumberSx,
  socialDialogPaperSx,
  socialDialogPrimaryButtonSx,
  socialDialogReconnectInfoSx,
  socialDialogRequirementCardSx,
  socialDialogSecondaryButtonSx,
  socialDialogTitleSx,
  socialDialogContentSx,
} from "./socialDialogUiSx";

// ============================================================
// PLATFORM CONFIGURATION
// ============================================================

// const PLATFORM_CONFIG = {
//   facebook: {
//     connect: {
//       title: "Connect Facebook",
//       continueLabel: "Continue with Facebook",
//       loadingLabel: "Connecting...",
//       message: "Your Facebook login will open in the next step.",

//       requirements: [
//         {
//           title: "Facebook account",
//           description:
//             "Make sure you can sign in to the Facebook account you want to use.",
//         },
//         {
//           title: "Facebook Page",
//           description:
//             "Make sure the Facebook Page you want to connect is already connected to a Business Portfolio.",
//         },
//         {
//           title: "Page access",
//           description:
//             "Make sure you have the required access to manage the Facebook Page.",
//         },
//       ],
//     },

//     reconnect: {
//       title: "Reconnect Facebook",
//       continueLabel: "Continue with Facebook",
//       loadingLabel: "Reconnecting...",
//       message:
//         "Your Facebook login will open in the next step. Make sure you are using the same Meta Business Portfolio that was previously used to connect this Page.",

//       requirements: [
//         {
//           title: "Same Meta Business Portfolio",
//           description:
//             "Make sure you are logged in to the same Meta Business Portfolio that was previously used to connect this Facebook Page.",
//         },
//         {
//           title: "Facebook Page",
//           description:
//             "Make sure the Facebook Page you want to reconnect is available in that Business Portfolio.",
//         },
//         {
//           title: "Page access",
//           description:
//             "Make sure you have the required access to manage the Facebook Page.",
//         },
//       ],
//     },
//   },

//   instagram: {
//     connect: {
//       title: "Connect Instagram",
//       continueLabel: "Continue with Instagram",
//       loadingLabel: "Connecting...",
//       message: "Your Instagram login will open in the next step.",

//       requirements: [
//         {
//           title: "Professional Instagram account",
//           description:
//             "Make sure the Instagram account you want to connect is a Professional account.",
//         },
//         {
//           title: "Instagram access",
//           description:
//             "Make sure you can sign in to the Instagram account you want to connect.",
//         },
//         {
//           title: "Authorization",
//           description:
//             "You'll need to authorize access to connect your Instagram account.",
//         },
//       ],
//     },

//     reconnect: {
//       title: "Reconnect Instagram",
//       continueLabel: "Continue with Instagram",
//       loadingLabel: "Reconnecting...",
//       message:
//         "Your Instagram login will open in the next step. Make sure you are logged in to the same Instagram account that was previously connected.",

//       requirements: [
//         {
//           title: "Same Instagram account",
//           description:
//             "Make sure you are logged in to the same Instagram account that was previously connected.",
//         },
//         {
//           title: "Professional Instagram account",
//           description:
//             "Make sure the Instagram account is still a Professional account.",
//         },
//         {
//           title: "Authorization",
//           description:
//             "You'll need to authorize access again to reconnect your Instagram account.",
//         },
//       ],
//     },
//   },
// };
const PLATFORM_CONFIG = {
  facebook: {
    connect: {
      title: "Connect Facebook",
      continueLabel: "Continue with Facebook",
      loadingLabel: "Connecting...",
      message:
        "Your Facebook login will open in the next step. You can then select the Pages you want to connect.",

      requirements: [
        {
          title: "Facebook account",
          description:
            "Make sure you can sign in to the Facebook account you want to use.",
        },
        {
          title: "Select Facebook Pages",
          description:
            "After signing in, select the Facebook Pages you want to connect to your organization.",
        },
        {
          title: "Page permissions",
          description:
            "Make sure you authorize the required permissions to manage and publish content to your selected Pages.",
        },
      ],
    },

    reconnect: {
      title: "Reconnect Facebook",
      continueLabel: "Continue with Facebook",
      loadingLabel: "Reconnecting...",
      message:
        "Your Facebook login will open in the next step. Make sure you use the same Facebook account that was previously connected.",

      requirements: [
        {
          title: "Same Facebook account",
          description:
            "Make sure you sign in to the same Facebook account that was previously used to connect this Page.",
        },
        {
          title: "Facebook Page access",
          description:
            "Make sure the previously connected Facebook Page is available to your account.",
        },
        {
          title: "Authorization",
          description:
            "Authorize the required permissions again to reconnect your Facebook Page.",
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
            "Authorize access to connect your Instagram account.",
        },
      ],
    },

    reconnect: {
      title: "Reconnect Instagram",
      continueLabel: "Continue with Instagram",
      loadingLabel: "Reconnecting...",
      message:
        "Your Instagram login will open in the next step. Make sure you use the same Instagram account that was previously connected.",

      requirements: [
        {
          title: "Same Instagram account",
          description:
            "Make sure you sign in to the same Instagram account that was previously connected.",
        },
        {
          title: "Professional Instagram account",
          description:
            "Make sure the Instagram account is still a Professional account.",
        },
        {
          title: "Authorization",
          description:
            "Authorize the required permissions again to reconnect your Instagram account.",
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
  const PlatformIcon = platform === "facebook" ? FacebookRoundedIcon : InstagramIcon;
  const platformIconTileSx = platform === "facebook"
    ? socialDialogFacebookIconTileSx
    : socialDialogInstagramIconTileSx;

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
      PaperProps={{ sx: socialDialogPaperSx }}
      aria-labelledby="social-account-dialog-title"
      aria-describedby="social-account-dialog-description"
    >
      {/* ======================================================
          TITLE
      ====================================================== */}

      <DialogTitle
        id="social-account-dialog-title"
        sx={socialDialogTitleSx}
      >
        <Box aria-hidden="true" sx={platformIconTileSx}>
          <PlatformIcon />
        </Box>
        <Typography component="span" sx={{ minWidth: 0, overflowWrap: "anywhere" }}>
          {config.title}
        </Typography>
      </DialogTitle>

      {/* ======================================================
          CONTENT
      ====================================================== */}

      <DialogContent
        id="social-account-dialog-description"
        sx={socialDialogContentSx}
      >
        {/* ====================================================
            INTRO
        ==================================================== */}

        <Typography
          variant="body2"
          sx={{
            mb: 2,
            color: "#64748B",
            fontSize: "0.875rem",
            fontWeight: 600,
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
            gap: 1.5,
          }}
        >
          {config.requirements.map((requirement, index) => (
            <Box
              key={requirement.title}
              sx={socialDialogRequirementCardSx}
            >
              {/* ==================================================
                  NUMBER
              ================================================== */}

              <Box
                sx={socialDialogNumberSx}
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
                    color: "#17294D",
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
                    color: "#657899",
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
            ...(mode === "reconnect" ? socialDialogReconnectInfoSx : socialDialogInfoSx),
          }}
        >
          <Typography
            variant="body2"
            sx={{
              fontSize: "0.8125rem",
              lineHeight: 1.6,
              color: mode === "reconnect" ? "#7C5B27" : "#475569",
            }}
          >
            {config.message}
          </Typography>
        </Box>
      </DialogContent>

      {/* ======================================================
          ACTIONS
      ====================================================== */}

      <DialogActions
        sx={socialDialogActionsSx}
      >
        {/* ====================================================
            CANCEL
        ==================================================== */}

        <Button
          type="button"
          variant="outlined"
          onClick={handleClose}
          disabled={isLoading}
          sx={socialDialogSecondaryButtonSx}
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
          sx={{ minWidth: { sm: 180 }, ...socialDialogPrimaryButtonSx }}
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
