import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  Box,
  Paper,
  Stack,
  Divider,
  CircularProgress,
  Alert,
} from "@mui/material";

import { FormProvider, useForm } from "react-hook-form";

import { zodResolver } from "@hookform/resolvers/zod";

import EditPlanHeader from "../../components/plans/edit/EditPlanHeader";

import PlanDetailsForm from "../../components/plans/create/PlanDetailsForm";
import PricingForm from "../../components/plans/create/PricingForm";
import PlanLimitsForm from "../../components/plans/create/PlanLimitsForm";
import PlanHighlightsForm from "../../components/plans/create/PlanHighlightsForm";

import EditPlanFooter from "../../components/plans/edit/EditPlanFooter";

import PlanLivePreview from "../../components/plans/create/PlanLivePreview";

import ConfirmDialog from "../../components/ui/dialog/ConfirmDialog";

import { planSchema } from "../../validation/plan.schema";
import { planDefaultValues } from "../../constants/forms/planDefaultValues";

import plansService from "../../services/plans.service";

export default function EditPlan() {
  const navigate = useNavigate();

  const { planId } = useParams();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const [loading, setLoading] = useState(true);

  const [submitLoading, setSubmitLoading] = useState(false);

  const [error, setError] = useState(null);

  const methods = useForm({
    resolver: zodResolver(planSchema),

    defaultValues: planDefaultValues,

    mode: "onSubmit",
  });

  /* =========================================
     LOAD PLAN
  ========================================= */

  useEffect(() => {
    let mounted = true;

    async function loadPlan() {
      try {
        setLoading(true);
        setError(null);

        const plan = await plansService.getPlan(planId);

        if (!plan) {
          navigate("/plans", {
            replace: true,
          });

          return;
        }

        if (!mounted) {
          return;
        }

        methods.reset({
          name: plan.name ?? "",
          description: plan.description ?? "",

          type: plan.type ?? "Basic",

          status: plan.status ?? "active",

          billing_cycle: plan.billing_cycle ?? "monthly",

          monthly_price: plan.monthly_price ?? "",

          yearly_price: plan.yearly_price ?? "",

          limits: {
            accounts: plan.limits?.accounts ?? "",

            posts: plan.limits?.posts ?? "",

            videos: plan.limits?.videos ?? "",

            ads: plan.limits?.ads ?? "",

            dm_automations: plan.limits?.dm_automations ?? "",
          },

          highlights: plan.highlights ?? "",
        });
      } catch (err) {
        console.error("Failed to load plan:", err);

        if (mounted) {
          setError(
            err?.response?.data?.message ||
              err?.message ||
              "Unable to load plan.",
          );
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadPlan();

    return () => {
      mounted = false;
    };
  }, [planId, navigate, methods]);

  /* =========================================
     UPDATE PLAN
  ========================================= */

  async function onSubmit(data) {
    try {
      setSubmitLoading(true);

      await plansService.updatePlan(planId, data);

      navigate("/plans");
    } catch (err) {
      console.error("Failed to update plan:", err);

      setError(
        err?.response?.data?.message ||
          err?.message ||
          "Failed to update plan.",
      );
    } finally {
      setSubmitLoading(false);
    }
  }

  /* =========================================
     DELETE PLAN
  ========================================= */

  async function handleDeletePlan() {
    try {
      await plansService.deletePlan(planId);

      setDeleteDialogOpen(false);

      navigate("/plans");
    } catch (err) {
      console.error("Failed to delete plan:", err);

      setError(
        err?.response?.data?.message ||
          err?.message ||
          "Failed to delete plan.",
      );

      setDeleteDialogOpen(false);
    }
  }

  /* =========================================
     LOADING
  ========================================= */

  if (loading) {
    return (
      <Box
        sx={{
          width: "100%",
          minHeight: 400,

          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <CircularProgress size={28} />
      </Box>
    );
  }

  /* =========================================
     ERROR
  ========================================= */

  if (error) {
    return (
      <Box
        sx={{
          width: "100%",
        }}
      >
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  /* =========================================
     PAGE
  ========================================= */

  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,

        boxSizing: "border-box",

        px: {
          xs: 2,
          sm: 3,
          md: 4,
        },
      }}
    >
      {/* =====================================
          HEADER
      ===================================== */}

      <EditPlanHeader onBack={() => navigate("/plans")} />

      {/* =====================================
          FORM
      ===================================== */}

      <FormProvider {...methods}>
        <Box
          component="form"
          onSubmit={methods.handleSubmit(onSubmit)}
          sx={{
            width: "100%",
            minWidth: 0,

            boxSizing: "border-box",
          }}
        >
          <Box
            sx={{
              width: "100%",
              minWidth: 0,

              display: "grid",

              gridTemplateColumns: {
                xs: "minmax(0, 1fr)",

                lg: "minmax(0, 1fr) 390px",
              },

              columnGap: {
                xs: 0,
                lg: 3,
              },

              rowGap: 3,

              alignItems: "start",
            }}
          >
            {/* =================================
                LEFT FORM
            ================================= */}

            <Stack
              spacing={3}
              sx={{
                width: "100%",
                minWidth: 0,
              }}
            >
              {/* PLAN DETAILS */}

              <Paper
                elevation={0}
                sx={{
                  width: "100%",

                  p: {
                    xs: 2.5,
                    sm: 3,
                  },

                  borderRadius: "18px",

                  border: "1px solid #E2E8F0",

                  backgroundColor: "#FFFFFF",

                  boxSizing: "border-box",
                }}
              >
                <PlanDetailsForm />
              </Paper>

              {/* PRICING */}

              <Paper
                elevation={0}
                sx={{
                  width: "100%",

                  p: {
                    xs: 2.5,
                    sm: 3,
                  },

                  borderRadius: "18px",

                  border: "1px solid #E2E8F0",

                  backgroundColor: "#FFFFFF",

                  boxSizing: "border-box",
                }}
              >
                <PricingForm />
              </Paper>

              {/* PLAN LIMITS */}

              <Paper
                elevation={0}
                sx={{
                  width: "100%",

                  p: {
                    xs: 2.5,
                    sm: 3,
                  },

                  borderRadius: "18px",

                  border: "1px solid #E2E8F0",

                  backgroundColor: "#FFFFFF",

                  boxSizing: "border-box",
                }}
              >
                <PlanLimitsForm />
              </Paper>

              {/* HIGHLIGHTS */}

              <Paper
                elevation={0}
                sx={{
                  width: "100%",

                  p: {
                    xs: 2.5,
                    sm: 3,
                  },

                  borderRadius: "18px",

                  border: "1px solid #E2E8F0",

                  backgroundColor: "#FFFFFF",

                  boxSizing: "border-box",
                }}
              >
                <PlanHighlightsForm />
              </Paper>

              {/* FOOTER */}

              <EditPlanFooter
                onCancel={() => navigate("/plans")}
                onDelete={() => setDeleteDialogOpen(true)}
                loading={submitLoading}
              />
            </Stack>

            {/* =================================
                RIGHT LIVE PREVIEW
            ================================= */}

            <Box
              sx={{
                width: "100%",
                minWidth: 0,

                position: "relative",
              }}
            >
              <PlanLivePreview />
            </Box>
          </Box>
        </Box>
      </FormProvider>

      {/* =====================================
          DELETE CONFIRMATION
      ===================================== */}

      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete Plan"
        message="Are you sure you want to delete this plan?"
        description="This action cannot be undone."
        confirmText="Delete"
        loading={false}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={handleDeletePlan}
      />
    </Box>
  );
}
