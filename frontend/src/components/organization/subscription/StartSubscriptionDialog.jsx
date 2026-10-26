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
import { glassPrimaryButtonSx } from "../../ui/form/glassFormSx";
import {
  glassDialogActionsSx,
  glassDialogCardSx,
  glassDialogContentSx,
  glassDialogPaperSx,
  glassDialogSecondaryButtonSx,
  glassDialogTitleSx,
  glassDialogToggleGroupSx,
} from "../../ui/dialog/glassDialogSx";

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
      PaperProps={{ sx: glassDialogPaperSx }}
    >
      <DialogTitle sx={glassDialogTitleSx}>
        Start Subscription
      </DialogTitle>

      <DialogContent dividers sx={glassDialogContentSx}>
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
              minHeight: 52,
              borderRadius: "14px",
              background: "linear-gradient(145deg, rgba(232,241,255,.78), rgba(255,255,255,.94))",
              "& .MuiOutlinedInput-notchedOutline": {
                borderColor: "rgba(142,164,204,.38)",
              },
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
            sx={glassDialogToggleGroupSx}
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

              ...glassDialogCardSx,
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

                color: "#0F172A",
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

      <DialogActions sx={glassDialogActionsSx}>
        <Button
          onClick={onClose}
          disabled={loading}
          color="inherit"
          sx={glassDialogSecondaryButtonSx}
        >
          Cancel
        </Button>

        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading || !planId || plans.length === 0}
          sx={{ minWidth: 150, ...glassPrimaryButtonSx }}
        >
          {loading ? "Starting..." : "Start Subscription"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
