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
                      border: "1px solid rgba(255,255,255,.94)",
                      background: "linear-gradient(145deg, rgba(255,255,255,.88), rgba(232,241,255,.8))",
                      boxShadow: "0 4px 10px rgba(76,101,145,.09), inset 0 1px 0 #fff, inset 0 -1px 2px rgba(104,126,169,.06)",
                      textTransform: "none",
                      fontSize: 14,
                      fontWeight: 600,
                      color: "#475569",
                      "&.Mui-selected": {
                        color: "#385FC0",
                        borderColor: "rgba(112,137,204,.58)",
                        background: "linear-gradient(145deg, #F0EAFF, #E4F0FF)",
                        boxShadow: "0 5px 12px rgba(93,107,180,.15), inset 0 1px 0 #fff, inset 0 -1px 2px rgba(113,128,190,.08)",
                        "&:hover": {
                          background: "linear-gradient(145deg, #F0EAFF, #E4F0FF)",
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
              borderRadius: "16px",
              border: "1px solid rgba(255,255,255,.96)",
              background: "linear-gradient(125deg, rgba(236,244,255,.88), rgba(249,242,255,.78) 62%, rgba(255,255,255,.82))",
              boxShadow: "0 7px 17px rgba(79,102,153,.10), inset 0 1px 0 rgba(255,255,255,.98), inset 0 -1px 0 rgba(129,151,193,.08)",
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
