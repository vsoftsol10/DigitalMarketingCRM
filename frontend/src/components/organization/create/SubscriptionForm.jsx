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

import CreditCardOutlinedIcon from "@mui/icons-material/CreditCardOutlined";

import FormSection from "../../ui/form/FormSection";
import FormSelect from "../../ui/form/FormSelect";

function formatPrice(value) {
  return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
}

function PriceCard({ label, value }) {
  return (
    <Paper
      elevation={0}
      sx={{
        flex: 1,
        minWidth: 0,

        p: 2,

        borderRadius: "14px",
        border: "1px solid #E2E8F0",
        backgroundColor: "#F8FAFC",
      }}
    >
      <Typography
        sx={{
          fontSize: "12px",
          fontWeight: 500,
          lineHeight: "18px",
          color: "#94A3B8",

          textTransform: "uppercase",
          letterSpacing: "0.04em",
        }}
      >
        {label}
      </Typography>

      <Typography
        sx={{
          mt: 0.35,

          fontSize: "20px",
          fontWeight: 700,
          lineHeight: "28px",

          color: "#1E293B",
        }}
      >
        ₹{formatPrice(value)}
      </Typography>
    </Paper>
  );
}

export default function SubscriptionForm({ plans = [] }) {
  const {
    control,
    formState: { errors },
  } = useFormContext();

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
    <FormSection
      icon={<CreditCardOutlinedIcon />}
      title="Subscription"
      description="Configure the organization's subscription plan and billing."
    >
      <Grid container spacing={3}>
        {/* =====================================================
            PLAN
        ===================================================== */}

        <Grid
          size={{
            xs: 12,
          }}
        >
          <FormSelect
            name="subscription_plan"
            label="Plan"
            required
            placeholder="Select Plan"
            options={planOptions}
          />
        </Grid>

        {/* =====================================================
            SELECTED PLAN PRICING
        ===================================================== */}

        {selectedPlan && (
          <Grid
            size={{
              xs: 12,
            }}
          >
            <Stack
              direction={{
                xs: "column",
                sm: "row",
              }}
              spacing={1.5}
            >
              <PriceCard label="Monthly" value={selectedPlan.monthly_price} />

              <PriceCard label="Yearly" value={selectedPlan.yearly_price} />
            </Stack>
          </Grid>
        )}

        {/* =====================================================
            BILLING CYCLE
        ===================================================== */}

        <Grid
          size={{
            xs: 12,
            md: 6,
          }}
        >
          <Box
            sx={{
              mb: 1,

              fontSize: 15,
              fontWeight: 500,

              color: "#334155",
            }}
          >
            Billing Cycle
          </Box>

          <Controller
            control={control}
            name="billing_cycle"
            render={({ field }) => (
              <ToggleButtonGroup
                exclusive
                fullWidth
                value={field.value}
                onChange={(_, value) => {
                  if (value) {
                    field.onChange(value);
                  }
                }}
                sx={{
                  gap: 1,

                  "& .MuiToggleButton-root": {
                    flex: 1,

                    height: 56,

                    borderRadius: "18px !important",

                    border: "1px solid #E2E8F0",

                    textTransform: "none",

                    fontSize: 18,
                    fontWeight: 500,

                    color: "#475569",

                    "&.Mui-selected": {
                      backgroundColor: "#EEF4FF",

                      color: "#2563EB",

                      border: "2px solid #2563EB",

                      "&:hover": {
                        backgroundColor: "#EEF4FF",
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
        </Grid>

        {/* =====================================================
            SELECTED BILLING PRICE
        ===================================================== */}

        {selectedPlan && (
          <Grid
            size={{
              xs: 12,
              md: 6,
            }}
          >
            <Box
              sx={{
                height: "100%",
                minHeight: 80,

                display: "flex",
                flexDirection: "column",
                justifyContent: "center",

                px: 2.25,

                borderRadius: "14px",

                backgroundColor: "#F8FAFC",

                border: "1px solid #E2E8F0",
              }}
            >
              <Typography
                sx={{
                  fontSize: "12px",
                  fontWeight: 500,
                  lineHeight: "18px",

                  color: "#94A3B8",

                  textTransform: "uppercase",

                  letterSpacing: "0.04em",
                }}
              >
                Selected Price
              </Typography>

              <Typography
                sx={{
                  mt: 0.2,

                  fontSize: "22px",
                  fontWeight: 700,
                  lineHeight: "30px",

                  color: "#1E293B",
                }}
              >
                ₹{formatPrice(selectedPrice)}
                <Typography
                  component="span"
                  sx={{
                    ml: 0.5,

                    fontSize: "14px",
                    fontWeight: 400,

                    color: "#94A3B8",
                  }}
                >
                  /{billingCycle === "yearly" ? "year" : "month"}
                </Typography>
              </Typography>
            </Box>
          </Grid>
        )}

        {/* =====================================================
            NO PLAN
        ===================================================== */}

        {!selectedPlan && (
          <Grid
            size={{
              xs: 12,
            }}
          >
            <Box
              sx={{
                p: 2,

                borderRadius: "14px",

                backgroundColor: "#F8FAFC",

                border: "1px dashed #CBD5E1",
              }}
            >
              <Typography
                sx={{
                  fontSize: "14px",
                  color: "#64748B",
                }}
              >
                Select a subscription plan to view pricing.
              </Typography>
            </Box>
          </Grid>
        )}
      </Grid>
    </FormSection>
  );
}
