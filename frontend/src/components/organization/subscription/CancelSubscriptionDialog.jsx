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
  glassDialogActionsSx,
  glassDialogCardSx,
  glassDialogContentSx,
  glassDialogDangerButtonSx,
  glassDialogPaperSx,
  glassDialogSecondaryButtonSx,
  glassDialogTitleSx,
} from "../../ui/dialog/glassDialogSx";

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
      PaperProps={{ sx: glassDialogPaperSx }}
    >
      <DialogTitle sx={glassDialogTitleSx}>
        Cancel Subscription
      </DialogTitle>

      <DialogContent dividers sx={glassDialogContentSx}>
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
            borderRadius: "14px",
            border: "1px solid rgba(246,202,134,.56)",
            background: "linear-gradient(145deg, rgba(255,250,235,.9), rgba(255,255,255,.76))",
            boxShadow: "0 4px 10px rgba(154,112,49,.06), inset 0 1px 0 #fff",
          }}
        >
          The current subscription will be cancelled immediately and preserved
          in subscription history. Any scheduled upcoming subscription will also
          be cancelled and will not be activated.
        </Alert>

        <Box sx={{ mt: 2.5, ...glassDialogCardSx }}>
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

      <DialogActions sx={glassDialogActionsSx}>
        <Button
          onClick={onClose}
          disabled={loading}
          color="inherit"
          sx={glassDialogSecondaryButtonSx}
        >
          Keep Subscription
        </Button>

        <Button
          variant="contained"
          color="error"
          onClick={onConfirm}
          disabled={loading}
          sx={{ minWidth: 150, ...glassDialogDangerButtonSx }}
        >
          {loading ? "Cancelling..." : "Cancel Subscription"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
