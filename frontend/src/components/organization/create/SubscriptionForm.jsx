import {
  Box,
  Grid,
  Paper,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";

import { Controller, useFormContext, useWatch } from "react-hook-form";

import FormSelect from "../../ui/form/FormSelect";
import {
  glassFieldErrorInputSx,
  glassFieldErrorMessageSx,
} from "../../ui/form/glassFormSx";

function formatPrice(value) {
  return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
}

function formatBillingCycle(value) {
  return value ? `${value[0].toUpperCase()}${value.slice(1)}` : "Not selected";
}

export default function SubscriptionForm({ plans = [] }) {
  const { control } = useFormContext();

  const selectedPlanId = useWatch({
    control,
    name: "subscription_plan",
  });

  const billingCycle = useWatch({
    control,
    name: "billing_cycle",
  });

  const selectedPlan =
    plans.find((plan) => String(plan.id) === String(selectedPlanId)) || null;

  const selectedPrice = selectedPlan
    ? billingCycle === "yearly"
      ? selectedPlan.yearly_price
      : selectedPlan.monthly_price
    : null;

  const planOptions = plans.map((plan) => ({
    value: plan.id,
    label: plan.name,
  }));

  return (
    <Box sx={{ width: "100%", minWidth: 0 }}>
      <Grid container spacing={{ xs: 2, md: 2.5 }} alignItems="stretch">
        <Grid size={{ xs: 12, md: 6 }}>
          <FormSelect
            name="subscription_plan"
            label="Plan"
            required
            placeholder="Select Plan"
            options={planOptions}
            errorInputSx={glassFieldErrorInputSx}
            errorMessageSx={glassFieldErrorMessageSx}
          />
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Stack spacing={0.75}>
            <Typography sx={{ fontSize: 14, fontWeight: 500, color: "#334155" }}>
              Billing Cycle
            </Typography>
            <Controller
              control={control}
              name="billing_cycle"
              render={({ field }) => (
                <ToggleButtonGroup
                  exclusive
                  fullWidth
                  value={field.value}
                  onChange={(_, value) => {
                    if (value) field.onChange(value);
                  }}
                  sx={{
                    gap: 0.75,
                    "& .MuiToggleButton-root": {
                      flex: 1,
                      minWidth: 0,
                      height: 52,
                      borderRadius: "12px !important",
                      border: "1px solid #DCE2EF",
                      background: "#FFFFFF",
                      boxShadow: "none",
                      textTransform: "none",
                      fontSize: 14,
                      fontWeight: 600,
                      color: "#475569",
                      "&.Mui-selected": {
                        color: "#6941D9",
                        borderColor: "#DAD1F8",
                        background: "#F5F2FF",
                        boxShadow: "none",
                        "&:hover": {
                          background: "#F5F2FF",
                        },
                      },
                    },
                  }}
                >
                  <ToggleButton value="monthly">Monthly</ToggleButton>
                  <ToggleButton value="yearly">Yearly</ToggleButton>
                </ToggleButtonGroup>
              )}
            />
          </Stack>
        </Grid>

        <Grid size={{ xs: 12 }}>
          <Paper
            elevation={0}
            sx={{
              minWidth: 0,
              p: { xs: 1.75, sm: 2 },
              borderRadius: "14px",
              border: "1px solid #E5E9F1",
              background: "#F8FAFC",
              boxShadow: "none",
            }}
          >
            <Stack
              direction={{ xs: "column", sm: "row" }}
              spacing={{ xs: 1, sm: 2 }}
              justifyContent="space-between"
              alignItems={{ xs: "flex-start", sm: "center" }}
            >
              <Box sx={{ minWidth: 0 }}>
                <Typography
                  sx={{
                    mb: 0.35,
                    color: "#7384A4",
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: ".07em",
                    textTransform: "uppercase",
                  }}
                >
                  Subscription Preview
                </Typography>
                {selectedPlan ? (
                  <Typography sx={{ color: "#25375C", fontSize: 15, fontWeight: 650 }}>
                    {selectedPlan.name} · {formatBillingCycle(billingCycle)} billing
                  </Typography>
                ) : (
                  <Typography sx={{ color: "#71809A", fontSize: 14 }}>
                    Select a plan to preview your subscription.
                  </Typography>
                )}
              </Box>
              {selectedPlan && (
                <Box sx={{ textAlign: { xs: "left", sm: "right" }, flexShrink: 0 }}>
                  <Typography sx={{ color: "#7C8BA8", fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".04em" }}>
                    Selected price
                  </Typography>
                  <Typography sx={{ color: "#4D5FB8", fontSize: 18, lineHeight: 1.35, fontWeight: 700 }}>
                    ₹{formatPrice(selectedPrice)}
                    <Typography component="span" sx={{ ml: 0.4, color: "#8290A9", fontSize: 12, fontWeight: 500 }}>
                      /{billingCycle === "yearly" ? "year" : "month"}
                    </Typography>
                  </Typography>
                </Box>
              )}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
