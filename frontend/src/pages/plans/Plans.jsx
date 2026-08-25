import {
  Alert,
  Box,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import plansService from "../../services/plans.service";

import PlansHeader from "../../components/plans/PlansHeader";
import PlansGrid from "../../components/plans/PlansGrid";

import { TYPOGRAPHY } from "../../theme/typography";

export default function Plans() {
  const navigate = useNavigate();

  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadPlans = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await plansService.getPlans();

      if (!Array.isArray(response)) {
        throw new Error("Invalid plans response.");
      }

      setPlans(response);
    } catch (error) {
      console.error("Failed to load plans:", error);

      setError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to load plans.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPlans();
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
        <CircularProgress size={28} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,
      }}
    >
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
          <Stack
            alignItems="center"
            justifyContent="center"
            sx={{
              minHeight: 300,
            }}
          >
            <Typography sx={TYPOGRAPHY.cardTitle}>
              No plans available
            </Typography>

            <Typography sx={TYPOGRAPHY.bodySmall}>
              Create your first subscription plan.
            </Typography>
          </Stack>
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