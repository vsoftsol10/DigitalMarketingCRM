import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";

import { useEffect, useState } from "react";

export default function RenewSubscriptionDialog({
  open,
  organization,
  loading = false,
  error = null,
  onClose,
  onSubmit,
}) {
  const [billingCycle, setBillingCycle] = useState(
    organization?.billing_cycle || "monthly",
  );

  useEffect(() => {
    if (open) {
      setBillingCycle(organization?.billing_cycle || "monthly");
    }
  }, [open, organization?.billing_cycle]);

  const handleSubmit = () => {
    onSubmit({
      billingCycle,
    });
  };

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
        Renew Subscription
      </DialogTitle>

      <DialogContent dividers>
        <Typography
          sx={{
            fontSize: 14,
            color: "#64748B",
            mb: 2.5,
          }}
        >
          Renew the current plan for the next billing period.
        </Typography>

        <Box
          sx={{
            mb: 2.5,
            p: 2,
            borderRadius: "12px",
            backgroundColor: "#F8FAFC",
            border: "1px solid #E2E8F0",
          }}
        >
          <Typography
            sx={{
              fontSize: 12,
              color: "#94A3B8",
              textTransform: "uppercase",
              fontWeight: 600,
              letterSpacing: "0.04em",
            }}
          >
            Current Plan
          </Typography>

          <Typography
            sx={{
              mt: 0.5,
              fontSize: 17,
              fontWeight: 700,
              color: "#0F172A",
            }}
          >
            {organization?.subscription_plan || "-"}
          </Typography>
        </Box>

        <Typography
          sx={{
            mb: 1,
            fontSize: 14,
            fontWeight: 600,
            color: "#334155",
          }}
        >
          Billing Cycle
        </Typography>

        <ToggleButtonGroup
          exclusive
          fullWidth
          value={billingCycle}
          onChange={(_, value) => {
            if (value) {
              setBillingCycle(value);
            }
          }}
          sx={{
            gap: 1,

            "& .MuiToggleButton-root": {
              flex: 1,
              minHeight: 48,

              borderRadius: "12px !important",

              border: "1px solid #E2E8F0",

              textTransform: "none",

              fontSize: 14,
              fontWeight: 600,
            },

            "& .MuiToggleButton-root.Mui-selected": {
              backgroundColor: "#EEF4FF",

              color: "#2563EB",

              border: "2px solid #2563EB",
            },
          }}
        >
          <ToggleButton value="monthly">Monthly</ToggleButton>

          <ToggleButton value="yearly">Yearly</ToggleButton>
        </ToggleButtonGroup>

        {error && (
          <Alert
            severity="error"
            sx={{
              mt: 3,
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
        <Button onClick={onClose} disabled={loading} color="inherit">
          Cancel
        </Button>

        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading}
          sx={{
            textTransform: "none",
            fontWeight: 600,
            boxShadow: "none",

            "&:hover": {
              boxShadow: "none",
            },
          }}
        >
          {loading ? "Renewing..." : "Renew Subscription"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
