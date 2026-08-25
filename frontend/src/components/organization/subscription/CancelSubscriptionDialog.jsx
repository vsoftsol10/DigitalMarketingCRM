import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";

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
    >
      <DialogTitle
        sx={{
          fontWeight: 700,
          color: "#0F172A",
        }}
      >
        Cancel Subscription
      </DialogTitle>

      <DialogContent dividers>
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
            borderRadius: "10px",
          }}
        >
          The current subscription will be cancelled immediately and preserved
          in subscription history. Any scheduled upcoming subscription will also
          be cancelled and will not be activated.
        </Alert>

        <Typography
          sx={{
            mt: 2.5,
            fontSize: 13,
            color: "#64748B",
          }}
        >
          Current Plan
        </Typography>

        <Typography
          sx={{
            mt: 0.35,
            fontSize: 17,
            fontWeight: 700,
            color: "#0F172A",
          }}
        >
          {organization.subscription_plan || "-"}
        </Typography>

        <Typography
          sx={{
            mt: 0.25,
            fontSize: 14,
            color: "#64748B",
            textTransform: "capitalize",
          }}
        >
          {organization.billing_cycle || "-"}
        </Typography>

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

      <DialogActions
        sx={{
          px: 3,
          py: 2,
          gap: 1,
        }}
      >
        <Button
          onClick={onClose}
          disabled={loading}
          color="inherit"
          sx={{
            textTransform: "none",
          }}
        >
          Keep Subscription
        </Button>

        <Button
          variant="contained"
          color="error"
          onClick={onConfirm}
          disabled={loading}
          sx={{
            minWidth: 150,

            textTransform: "none",

            fontWeight: 600,

            boxShadow: "none",

            "&:hover": {
              boxShadow: "none",
            },
          }}
        >
          {loading ? "Cancelling..." : "Cancel Subscription"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
