import { Box, Paper, Stack } from "@mui/material";

import { FormProvider, useForm } from "react-hook-form";

import { zodResolver } from "@hookform/resolvers/zod";

import { useNavigate, useSearchParams } from "react-router-dom";

import CreatePlanHeader from "../../components/plans/create/CreatePlanHeader";
import PlanDetailsForm from "../../components/plans/create/PlanDetailsForm";
import PricingForm from "../../components/plans/create/PricingForm";
import PlanLimitsForm from "../../components/plans/create/PlanLimitsForm";
import PlanHighlightsForm from "../../components/plans/create/PlanHighlightsForm";
import CreatePlanFooter from "../../components/plans/create/CreatePlanFooter";
import PlanLivePreview from "../../components/plans/create/PlanLivePreview";

import { planSchema } from "../../validation/plan.schema";
import { planDefaultValues } from "../../constants/forms/planDefaultValues";

import plansService from "../../services/plans.service";
import { planSectionSx } from "../../components/plans/plansGlassSx";

export default function CreatePlan() {
  const navigate = useNavigate();

  const [searchParams] = useSearchParams();

  const customPlan = searchParams.get("type") === "custom";

  const methods = useForm({
    resolver: zodResolver(planSchema),

    defaultValues: {
      ...planDefaultValues,

      ...(customPlan
        ? {
            type: "Custom",
          }
        : {}),
    },

    mode: "onSubmit",
  });

  const { setError, formState: { isSubmitting } } = methods;

  async function onSubmit(data) {
    try {
      const payload = { ...data };

      if (customPlan) {
        delete payload.type;
      }

      await plansService.createPlan(payload, {
        custom: customPlan,
      });

      navigate("/plans");
    } catch (error) {
      console.error("Failed to create plan:", error);

      const responseData = error?.response?.data;
      const backendErrors = responseData?.errors;

      if (backendErrors && typeof backendErrors === "object") {
        Object.entries(backendErrors).forEach(([field, messages]) => {
          const message = Array.isArray(messages)
            ? messages[0]
            : String(messages);
          const frontendField = mapBackendFieldToFrontend(field);

          if (frontendField) {
            setError(frontendField, {
              type: "server",
              message,
            });
          }
        });
      }

      setError("root.server", {
        type: "server",
        message:
          responseData?.message ||
          error?.message ||
          "Unable to create plan. Please try again.",
      });
    }
  }

  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,
        boxSizing: "border-box",

        pb: 2,
      }}
    >
      {/* =========================
          PAGE HEADER
      ========================= */}

      <CreatePlanHeader onBack={() => navigate("/plans")} />

      {/* =========================
          FORM
      ========================= */}

      <FormProvider {...methods}>
        <Box
          component="form"
          onSubmit={methods.handleSubmit(onSubmit)}
          sx={{
            width: "100%",
            minWidth: 0,
          }}
        >
          <Box
            sx={{
              width: "100%",
              display: "grid",

              gridTemplateColumns: {
                xs: "1fr",
                lg: "minmax(0, 1fr) 390px",
              },

              columnGap: 3,
              rowGap: 3,

              alignItems: "start",
            }}
          >
            {/* =====================================
          LEFT FORM CONTENT
      ===================================== */}

            <Stack
              spacing={3}
              sx={{
                width: "100%",
                minWidth: 0,
                gridColumn: {
                  xs: "1",
                  lg: "1",
                },
              }}
            >
              {/* PLAN DETAILS */}

              <Paper
                elevation={0}
                sx={planSectionSx}
              >
                <PlanDetailsForm customPlan={customPlan} />
              </Paper>

              {/* PRICING */}

              <Paper
                elevation={0}
                sx={planSectionSx}
              >
                <PricingForm />
              </Paper>

              {/* LIMITS */}

              <Paper
                elevation={0}
                sx={planSectionSx}
              >
                <PlanLimitsForm />
              </Paper>

              {/* HIGHLIGHTS */}

              <Paper
                elevation={0}
                sx={planSectionSx}
              >
                <PlanHighlightsForm />
              </Paper>
            </Stack>

            {/* =====================================
          RIGHT LIVE PREVIEW
      ===================================== */}

            <Box
              sx={{
                width: "100%",
                minWidth: 0,

                gridColumn: {
                  xs: "1",
                  lg: "2",
                },

                gridRow: {
                  xs: "auto",
                  lg: "1 / span 2",
                },
              }}
            >
              <PlanLivePreview />
            </Box>

            {/* =====================================
          FOOTER
          IMPORTANT:
          Separate grid item
      ===================================== */}

            <Box
              sx={{
                width: "100%",
                minWidth: 0,

                gridColumn: {
                  xs: "1",
                  lg: "1",
                },

                display: "flex",
                justifyContent: "flex-end",
                alignItems: "center",

                mt: 0,
              }}
            >
              <CreatePlanFooter onCancel={() => navigate("/plans")} loading={isSubmitting} />
            </Box>
          </Box>
        </Box>
      </FormProvider>
    </Box>
  );
}

function mapBackendFieldToFrontend(field) {
  const fieldMap = {
    plan_type: "type",
  };

  return fieldMap[field] || field;
}
