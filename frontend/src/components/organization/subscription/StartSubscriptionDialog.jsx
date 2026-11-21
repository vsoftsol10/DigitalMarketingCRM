import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";

import { useEffect, useMemo, useState } from "react";
import {
  subscriptionDialogActionsSx,
  subscriptionDialogCardSx,
  subscriptionDialogContentSx,
  subscriptionDialogPaperSx,
  subscriptionDialogPrimaryButtonSx,
  subscriptionDialogSecondaryButtonSx,
  subscriptionDialogSelectSx,
  subscriptionDialogTitleSx,
  subscriptionDialogToggleGroupSx,
} from "../organizationUiSx";

function formatPrice(value) {
  return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
}

export default function StartSubscriptionDialog({
  open,
  plans = [],
  loading = false,
  error = null,
  onClose,
  onSubmit,
}) {
  const [planId, setPlanId] = useState("");

  const [billingCycle, setBillingCycle] = useState("monthly");

  useEffect(() => {
    if (!open) {
      return;
    }

    setPlanId(plans[0]?.id || "");

    setBillingCycle("monthly");
  }, [open, plans]);

  const selectedPlan = useMemo(
    () => plans.find((plan) => String(plan.id) === String(planId)) || null,
    [plans, planId],
  );

  const selectedPrice = selectedPlan
    ? billingCycle === "yearly"
      ? selectedPlan.yearly_price
      : selectedPlan.monthly_price
    : null;

  const handleSubmit = () => {
    if (!planId) {
      return;
    }

    onSubmit({
      plan: planId,
      billingCycle,
    });
  };

  return (
    <Dialog
      open={open}
      onClose={loading ? undefined : onClose}
      fullWidth
      maxWidth="sm"
      PaperProps={{ sx: subscriptionDialogPaperSx }}
    >
      <DialogTitle sx={subscriptionDialogTitleSx}>
        Start Subscription
      </DialogTitle>

      <DialogContent dividers sx={subscriptionDialogContentSx}>
        <Typography
          sx={{
            mb: 3,
            fontSize: 14,
            lineHeight: "22px",
            color: "#64748B",
          }}
        >
          Start a new subscription for this organization.
        </Typography>

        {/* =====================================================
            PLAN
        ===================================================== */}

        <FormControl
          fullWidth
          required
          disabled={loading || plans.length === 0}
        >
          <InputLabel>Plan</InputLabel>

          <Select
            value={planId}
            label="Plan"
            onChange={(event) => setPlanId(event.target.value)}
            sx={{
              ...subscriptionDialogSelectSx,
              "& .MuiOutlinedInput-notchedOutline": {
                borderColor: "#DCE2EF",
              },
              "&:hover .MuiOutlinedInput-notchedOutline": { borderColor: "#B8C3D8" },
              "&.Mui-focused .MuiOutlinedInput-notchedOutline": { borderColor: "#7B61E8" },
            }}
          >
            {plans.map((plan) => (
              <MenuItem key={plan.id} value={plan.id}>
                {plan.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* =====================================================
            BILLING CYCLE
        ===================================================== */}

        <Box
          sx={{
            mt: 3,
          }}
        >
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
            disabled={loading}
            sx={subscriptionDialogToggleGroupSx}
          >
            <ToggleButton value="monthly">Monthly</ToggleButton>

            <ToggleButton value="yearly">Yearly</ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {/* =====================================================
            PRICE
        ===================================================== */}

        {selectedPlan && (
          <Box
            sx={{
              mt: 3,
              p: 2,

              borderRadius: "12px",

              ...subscriptionDialogCardSx,
            }}
          >
            <Typography
              sx={{
                fontSize: 12,
                fontWeight: 600,

                color: "#94A3B8",

                textTransform: "uppercase",

                letterSpacing: "0.04em",
              }}
            >
              Selected Price
            </Typography>

            <Typography
              sx={{
                mt: 0.5,

                fontSize: 22,
                lineHeight: "30px",
                fontWeight: 700,

                color: "#6941D9",
              }}
            >
              ₹{formatPrice(selectedPrice)}
              <Typography
                component="span"
                sx={{
                  ml: 0.5,

                  fontSize: 14,
                  fontWeight: 400,

                  color: "#94A3B8",
                }}
              >
                /{billingCycle === "yearly" ? "year" : "month"}
              </Typography>
            </Typography>
          </Box>
        )}

        {/* =====================================================
            NO ACTIVE PLANS
        ===================================================== */}

        {plans.length === 0 && (
          <Alert
            severity="warning"
            sx={{
              mt: 3,
              borderRadius: "10px",
            }}
          >
            No active subscription plans are available.
          </Alert>
        )}

        {/* =====================================================
            ERROR
        ===================================================== */}

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

      {/* =======================================================
          ACTIONS
      ======================================================= */}

      <DialogActions sx={subscriptionDialogActionsSx}>
        <Button
          onClick={onClose}
          disabled={loading}
          color="inherit"
          sx={subscriptionDialogSecondaryButtonSx}
        >
          Cancel
        </Button>

        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading || !planId || plans.length === 0}
          sx={{ minWidth: { sm: 150 }, ...subscriptionDialogPrimaryButtonSx }}
        >
          {loading ? "Starting..." : "Start Subscription"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
