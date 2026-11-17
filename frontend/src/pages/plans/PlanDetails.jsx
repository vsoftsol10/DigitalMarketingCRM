import { Alert, Box } from "@mui/material";

import { useEffect, useState } from "react";

import { useNavigate, useParams } from "react-router-dom";

import plansService from "../../services/plans.service";

import PlanDetailsHeader from "../../components/plans/details/PlanDetailsHeader";
import PlanSummaryCard from "../../components/plans/details/PlanSummaryCard";
import PlanDetailsCard from "../../components/plans/details/PlanDetailsCard";

import ConfirmDialog from "../../components/ui/dialog/ConfirmDialog";
import LoadingState from "../../components/ui/LoadingState";
import ErrorState from "../../components/ui/ErrorState";
import { formatApiErrorMessage } from "../../utils/apiErrorMessage";

export default function PlanDetails() {
  const navigate = useNavigate();
  const { planId } = useParams();

  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [loadAttempt, setLoadAttempt] = useState(0);

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function loadPlan() {
      try {
        setLoading(true);
        setLoadError(null);

        const response = await plansService.getPlan(planId);

        if (!response) {
          navigate("/plans", {
            replace: true,
          });
          return;
        }

        if (mounted) {
          setPlan(response);
        }
      } catch (error) {
        console.error("Failed to load plan:", error);

        if (mounted) {
          setLoadError(formatApiErrorMessage(error, {
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
  }, [planId, navigate, loadAttempt]);

  const handleDelete = async () => {
    try {
      setDeleteLoading(true);
      setError(null);

      await plansService.deletePlan(plan.id);

      setDeleteDialogOpen(false);

      navigate("/plans", {
        replace: true,
      });
    } catch (error) {
      console.error("Failed to delete plan:", error);

      setError(formatApiErrorMessage(error, {
        fallback: "Unable to delete plan.",
      }));

      setDeleteDialogOpen(false);
    } finally {
      setDeleteLoading(false);
    }
  };

  if (loading) {
    return <LoadingState page="Plan Details" />;
  }

  if (loadError) {
    return <ErrorState message={loadError} onRetry={() => setLoadAttempt((attempt) => attempt + 1)} variant="page" />;
  }

  if (!plan) {
    return null;
  }

  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,

        /*
         * Original UI content width.
         * Header + cards same alignment.
         */
        maxWidth: 1120,

        mx: "auto",

        px: {
          xs: 2,
          sm: 2,
          md: 0,
        },
      }}
    >
      {error && (
        <Alert severity="error" role="alert" sx={{ mb: 3, borderRadius: "12px" }}>
          {formatApiErrorMessage(error, {
            fallback: "Unable to delete plan.",
          })}
        </Alert>
      )}

      <PlanDetailsHeader
        plan={plan}
        onBack={() => navigate("/plans")}
        onEdit={() => navigate(`/plans/${plan.id}/edit`)}
        onDelete={() => {
          setError(null);
          setDeleteDialogOpen(true);
        }}
      />

      <Box
        sx={{
          display: "grid",

          gridTemplateColumns: {
            xs: "1fr",
            md: "minmax(0, 1fr) 330px",
          },

          gap: {
            xs: 2.5,
            md: 3,
          },

          mt: 3,

          alignItems: "start",
        }}
      >
        <PlanDetailsCard plan={plan} />

        <PlanSummaryCard plan={plan} />
      </Box>

      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete Plan"
        message={`Are you sure you want to delete "${plan.name}"?`}
        description="This action cannot be undone."
        confirmText="Delete"
        loading={deleteLoading}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={handleDelete}
      />
    </Box>
  );
}
