import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  Box,
  Paper,
  Stack,
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
import LoadingState from "../../components/ui/LoadingState";

import PlanLivePreview from "../../components/plans/create/PlanLivePreview";

import ConfirmDialog from "../../components/ui/dialog/ConfirmDialog";
import ErrorState from "../../components/ui/ErrorState";

import { planSchema } from "../../validation/plan.schema";
import { planDefaultValues } from "../../constants/forms/planDefaultValues";

import plansService from "../../services/plans.service";
import { formatApiErrorMessage } from "../../utils/apiErrorMessage";
import { planSectionSx } from "../../components/plans/plansGlassSx";

export default function EditPlan() {
  const navigate = useNavigate();

  const { planId } = useParams();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const [loading, setLoading] = useState(true);

  const [submitLoading, setSubmitLoading] = useState(false);

  const [updateError, setUpdateError] = useState(null);
  const [deleteError, setDeleteError] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [loadAttempt, setLoadAttempt] = useState(0);

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
        setLoadError(null);

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
          setLoadError(formatApiErrorMessage(err, {
            fallback: "Unable to load plan.",
          }));
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
  }, [planId, navigate, methods, loadAttempt]);

  /* =========================================
     UPDATE PLAN
  ========================================= */

  async function onSubmit(data) {
    try {
      setSubmitLoading(true);
      setUpdateError(null);

      await plansService.updatePlan(planId, data);

      navigate("/plans");
    } catch (err) {
      console.error("Failed to update plan:", err);

      setUpdateError(formatApiErrorMessage(err, {
        fallback: "Failed to update plan.",
      }));
    } finally {
      setSubmitLoading(false);
    }
  }

  /* =========================================
     DELETE PLAN
  ========================================= */

  async function handleDeletePlan() {
    try {
      setDeleteError(null);

      await plansService.deletePlan(planId);

      setDeleteDialogOpen(false);

      navigate("/plans");
    } catch (err) {
      console.error("Failed to delete plan:", err);

      setDeleteError(formatApiErrorMessage(err, {
        fallback: "Failed to delete plan.",
      }));

      setDeleteDialogOpen(false);
    }
  }

  /* =========================================
     LOADING
  ========================================= */

  if (loading) {
    return <LoadingState page="Edit Plan" />;
  }

  if (loadError) {
    return <ErrorState message={loadError} onRetry={() => setLoadAttempt((attempt) => attempt + 1)} variant="page" />;
  }

  /* =========================================
     PAGE
  ========================================= */

  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,
        maxWidth: 1340,

        boxSizing: "border-box",

        pb: 2,
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
          onSubmit={(event) => {
            setUpdateError(null);
            return methods.handleSubmit(onSubmit)(event);
          }}
          onChange={() => {
            if (updateError) {
              setUpdateError(null);
            }
          }}
          sx={{
            width: "100%",
            minWidth: 0,

            boxSizing: "border-box",
          }}
        >
          {updateError && (
            <Alert severity="error" role="alert" sx={{ mb: 3, borderRadius: "12px" }}>
              {updateError}
            </Alert>
          )}

          {deleteError && (
            <Alert severity="error" role="alert" sx={{ mb: 3, borderRadius: "12px" }}>
              {deleteError}
            </Alert>
          )}

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
                sx={planSectionSx}
              >
                <PlanDetailsForm />
              </Paper>

              {/* PRICING */}

              <Paper
                elevation={0}
                sx={planSectionSx}
              >
                <PricingForm />
              </Paper>

              {/* PLAN LIMITS */}

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

              {/* FOOTER */}

              <EditPlanFooter
                onCancel={() => navigate("/plans")}
                onDelete={() => {
                  setDeleteError(null);
                  setDeleteDialogOpen(true);
                }}
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
        crmStyle
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
