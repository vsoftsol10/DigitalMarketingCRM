import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";
import {
  subscriptionDialogActionsSx,
  subscriptionDialogCardSx,
  subscriptionDialogContentSx,
  subscriptionDialogDangerButtonSx,
  subscriptionDialogPaperSx,
  subscriptionDialogSecondaryButtonSx,
  subscriptionDialogTitleSx,
} from "../organizationUiSx";

export default function CancelSubscriptionDialog({
  open,
  organization,
  loading = false,
  error = null,
  onClose,
  onConfirm,
}) {
  if (!organization) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onClose={loading ? undefined : onClose}
      fullWidth
      maxWidth="sm"
      PaperProps={{ sx: subscriptionDialogPaperSx }}
    >
      <DialogTitle sx={subscriptionDialogTitleSx}>
        Cancel Subscription
      </DialogTitle>

      <DialogContent dividers sx={subscriptionDialogContentSx}>
        <Typography
          sx={{
            fontSize: 15,
            lineHeight: "24px",
            color: "#334155",
          }}
        >
          Are you sure you want to cancel the current subscription?
        </Typography>

        <Alert
          severity="warning"
          sx={{
            mt: 2.5,
            borderRadius: "12px",
            border: "1px solid #F5D5D5",
            background: "#FFFBFB",
            color: "#7F1D1D",
            boxShadow: "none",
            "& .MuiAlert-icon": { color: "#D64545" },
          }}
        >
          The current subscription will be cancelled immediately and preserved
          in subscription history. Any scheduled upcoming subscription will also
          be cancelled and will not be activated.
        </Alert>

        <Box sx={{ mt: 2.5, ...subscriptionDialogCardSx }}>
          <Typography
            sx={{
              fontSize: 12,
              fontWeight: 600,
              color: "#8192B0",
              textTransform: "uppercase",
              letterSpacing: "0.04em",
            }}
          >
            Current Plan
          </Typography>
          <Typography
            sx={{
              mt: 0.35,
              fontSize: 17,
              fontWeight: 700,
              color: "#17294D",
            }}
          >
            {organization.subscription_plan || "-"}
          </Typography>
          <Typography
            sx={{
              mt: 0.25,
              fontSize: 14,
              color: "#657899",
              textTransform: "capitalize",
            }}
          >
            {organization.billing_cycle || "-"}
          </Typography>
        </Box>

        {error && (
          <Alert
            severity="error"
            sx={{
              mt: 2.5,
              borderRadius: "10px",
            }}
          >
            {error}
          </Alert>
        )}
      </DialogContent>

      <DialogActions sx={subscriptionDialogActionsSx}>
        <Button
          onClick={onClose}
          disabled={loading}
          color="inherit"
          sx={subscriptionDialogSecondaryButtonSx}
        >
          Keep Subscription
        </Button>

        <Button
          variant="contained"
          color="error"
          onClick={onConfirm}
          disabled={loading}
          sx={{ minWidth: { sm: 150 }, ...subscriptionDialogDangerButtonSx }}
        >
          {loading ? "Cancelling..." : "Cancel Subscription"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
