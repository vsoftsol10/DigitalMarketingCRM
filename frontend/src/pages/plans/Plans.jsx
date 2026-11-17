import { Box } from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import plansService from "../../services/plans.service";

import PlansHeader from "../../components/plans/PlansHeader";
import LoadingState from "../../components/ui/LoadingState";
import ErrorState from "../../components/ui/ErrorState";
import EmptyState from "../../components/ui/EmptyState";
import PlansGrid from "../../components/plans/PlansGrid";

import { formatApiErrorMessage } from "../../utils/apiErrorMessage";

export default function Plans() {
  const navigate = useNavigate();

  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasLoadedSuccessfully, setHasLoadedSuccessfully] = useState(false);

  const loadPlans = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await plansService.getPlans();

      if (!Array.isArray(response)) {
        throw new Error("Invalid plans response.");
      }

      setPlans(response);
      setHasLoadedSuccessfully(true);
    } catch (error) {
      console.error("Failed to load plans:", error);

      setError(formatApiErrorMessage(error, {
        fallback: "Unable to load plans.",
      }));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    Promise.resolve().then(() => {
      if (active) loadPlans();
    });

    return () => {
      active = false;
    };
  }, [loadPlans]);

  const handleCreatePlan = () => {
    navigate("/plans/new");
  };

  const handleCustomPlan = () => {
    navigate("/plans/new?type=custom");
  };

  const handleSelectPlan = (plan) => {
    navigate(`/plans/${plan.id}`);
  };

  if (loading && !hasLoadedSuccessfully) {
    return <LoadingState page="Plans" />;
  }

  if (error && !hasLoadedSuccessfully) {
    return <ErrorState message={error} onRetry={loadPlans} variant="page" />;
  }

  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,
      }}
    >
      {error && <ErrorState message={error} onRetry={loadPlans} variant="inline" />}
      {loading && <LoadingState label="UPDATING PLANS..." variant="inline" />}
      <PlansHeader
        onCustomPlan={handleCustomPlan}
        onCreatePlan={handleCreatePlan}
      />

      {/* Plans Grid */}
      <Box
        sx={{
          mt: 3,
        }}
      >
        {plans.length === 0 ? (
          !loading && hasLoadedSuccessfully && !error ? (
            <EmptyState
              title="No plans available"
              description="Create your first subscription plan."
              sx={{ minHeight: 300 }}
            />
          ) : null
        ) : (
          <PlansGrid
            plans={plans}
            onSelect={handleSelectPlan}
          />
        )}
      </Box>
    </Box>
  );
}
