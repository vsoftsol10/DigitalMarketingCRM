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
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";

import { useEffect, useMemo, useState } from "react";

function formatPrice(value) {
  return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
}

export default function ChangePlanDialog({
  open,
  organization,
  plans = [],
  loading = false,
  error = null,
  onClose,
  onSubmit,
}) {
  const [planId, setPlanId] = useState("");

  const [billingCycle, setBillingCycle] = useState(
    organization?.billing_cycle || "monthly",
  );

  useEffect(() => {
    if (!open) {
      return;
    }

    const currentPlanName = organization?.subscription_plan?.toLowerCase();

    const currentPlan = plans.find(
      (plan) => plan.name?.toLowerCase() === currentPlanName,
    );

    setPlanId(currentPlan?.id || "");

    setBillingCycle(organization?.billing_cycle || "monthly");
  }, [
    open,
    organization?.subscription_plan,
    organization?.billing_cycle,
    plans,
  ]);

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
    >
      <DialogTitle
        sx={{
          fontWeight: 700,
          color: "#0F172A",
        }}
      >
        Change Subscription Plan
      </DialogTitle>

      <DialogContent dividers>
        <Typography
          sx={{
            mb: 3,
            fontSize: 14,
            lineHeight: "22px",
            color: "#64748B",
          }}
        >
          Choose a new plan and billing cycle. The current subscription will
          remain in history.
        </Typography>

        {/* =====================================================
            CURRENT SUBSCRIPTION
        ===================================================== */}

        <Box
          sx={{
            mb: 3,
            p: 2,

            borderRadius: "12px",

            backgroundColor: "#F8FAFC",

            border: "1px solid #E2E8F0",
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
            Current Subscription
          </Typography>

          <Typography
            sx={{
              mt: 0.5,

              fontSize: 16,
              fontWeight: 700,

              color: "#0F172A",
            }}
          >
            {organization?.subscription_plan || "-"}
          </Typography>

          <Typography
            sx={{
              mt: 0.25,

              fontSize: 13,
              color: "#64748B",

              textTransform: "capitalize",
            }}
          >
            {organization?.billing_cycle || "-"}
          </Typography>
        </Box>

        {/* =====================================================
            PLAN
        ===================================================== */}

        <FormControl fullWidth required disabled={loading}>
          <InputLabel>New Plan</InputLabel>

          <Select
            value={planId}
            label="New Plan"
            onChange={(event) => setPlanId(event.target.value)}
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

                color: "#475569",
              },

              "& .MuiToggleButton-root.Mui-selected": {
                backgroundColor: "#EEF4FF",

                color: "#2563EB",

                border: "2px solid #2563EB",

                "&:hover": {
                  backgroundColor: "#EEF4FF",
                },
              },
            }}
          >
            <ToggleButton value="monthly">Monthly</ToggleButton>

            <ToggleButton value="yearly">Yearly</ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {/* =====================================================
            SELECTED PLAN PRICE
        ===================================================== */}

        {selectedPlan && (
          <Box
            sx={{
              mt: 3,
              p: 2,

              borderRadius: "12px",

              backgroundColor: "#F8FAFC",

              border: "1px solid #E2E8F0",
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
            VALIDATION / SERVER ERROR
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

      {/* =====================================================
          ACTIONS
      ===================================================== */}

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
          Cancel
        </Button>

        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading || !planId}
          sx={{
            minWidth: 130,

            textTransform: "none",

            fontWeight: 600,

            boxShadow: "none",

            "&:hover": {
              boxShadow: "none",
            },
          }}
        >
          {loading ? "Changing..." : "Change Plan"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
