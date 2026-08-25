import { Alert, Box, CircularProgress } from "@mui/material";

import { useEffect, useState } from "react";

import { useNavigate, useParams } from "react-router-dom";

import plansService from "../../services/plans.service";

import PlanDetailsHeader from "../../components/plans/details/PlanDetailsHeader";
import PlanSummaryCard from "../../components/plans/details/PlanSummaryCard";
import PlanDetailsCard from "../../components/plans/details/PlanDetailsCard";

import ConfirmDialog from "../../components/ui/dialog/ConfirmDialog";

export default function PlanDetails() {
  const navigate = useNavigate();
  const { planId } = useParams();

  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function loadPlan() {
      try {
        setLoading(true);
        setError(null);

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
          setError(
            error?.response?.data?.message ||
              error?.message ||
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
  }, [planId, navigate]);

  const handleDelete = async () => {
    try {
      setDeleteLoading(true);

      await plansService.deletePlan(plan.id);

      setDeleteDialogOpen(false);

      navigate("/plans", {
        replace: true,
      });
    } catch (error) {
      console.error("Failed to delete plan:", error);

      setError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to delete plan.",
      );

      setDeleteDialogOpen(false);
    } finally {
      setDeleteLoading(false);
    }
  };

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: 400,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <CircularProgress size={26} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ width: "100%" }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
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
        maxWidth: 970,

        mx: "auto",

        px: {
          xs: 2,
          sm: 2,
          md: 0,
        },
      }}
    >
      <PlanDetailsHeader
        plan={plan}
        onBack={() => navigate("/plans")}
        onEdit={() => navigate(`/plans/${plan.id}/edit`)}
        onDelete={() => setDeleteDialogOpen(true)}
      />

      <Box
        sx={{
          display: "grid",

          gridTemplateColumns: {
            xs: "1fr",
            md: "minmax(0, 1fr) 300px",
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
