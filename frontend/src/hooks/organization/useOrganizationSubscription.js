import { useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import organizationService from "../../services/organization/organization.service";
import { NOTIFICATION_QUERY_KEY } from "../../services/notification.service";
import formatApiErrorMessage from "../../utils/apiErrorMessage";

export default function useOrganizationSubscription({
  organizationId,
  onSuccess,
}) {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);

  const [error, setError] = useState(null);

  // ============================================================
  // HISTORY STATE
  // ============================================================

  const [history, setHistory] = useState([]);

  const [historyLoaded, setHistoryLoaded] = useState(false);

  const [historyOrganizationId, setHistoryOrganizationId] = useState(null);

  const [historyLoading, setHistoryLoading] = useState(false);

  const [historyError, setHistoryError] = useState(null);

  // ============================================================
  // COMMON ACTION EXECUTOR
  // ============================================================

  const execute = useCallback(
    async (callback, { refreshNotifications = false } = {}) => {
      if (!organizationId) {
        setError("Organization ID is required.");

        return null;
      }

      if (loading) {
        return null;
      }

      try {
        setLoading(true);
        setError(null);

        const response = await callback();

        if (!response?.success) {
          throw new Error(response?.message || "Subscription action failed.");
        }

        if (refreshNotifications) {
          void queryClient.invalidateQueries({ queryKey: NOTIFICATION_QUERY_KEY });
        }

        await onSuccess?.(response);

        return response;
      } catch (error) {
        console.error("Subscription action failed:", error);

        const message =
          error?.response?.data?.message ||
          error?.message ||
          "Subscription action failed.";

        setError(message);

        return null;
      } finally {
        setLoading(false);
      }
    },
    [organizationId, loading, onSuccess, queryClient],
  );

  // ============================================================
  // RENEW
  // ============================================================

  const renew = useCallback(
    async ({ billingCycle } = {}) => {
      return execute(
        () => organizationService.renewSubscription(
          organizationId,
          billingCycle
            ? {
                billing_cycle: billingCycle,
              }
            : {},
        ),
        { refreshNotifications: true },
      );
    },
    [organizationId, execute],
  );

  // ============================================================
  // CHANGE PLAN
  // ============================================================

  const changePlan = useCallback(
    async ({ plan, billingCycle }) => {
      return execute(() =>
        organizationService.changeSubscriptionPlan(organizationId, {
          plan,
          billing_cycle: billingCycle,
        }),
      );
    },
    [organizationId, execute],
  );

  // ============================================================
  // START
  // ============================================================

  const start = useCallback(
    async ({ plan, billingCycle }) => {
      return execute(
        () => organizationService.startSubscription(organizationId, {
          plan,
          billing_cycle: billingCycle,
        }),
        { refreshNotifications: true },
      );
    },
    [organizationId, execute],
  );

  // ============================================================
  // CANCEL
  // ============================================================

  const cancel = useCallback(async () => {
    return execute(() =>
      organizationService.cancelSubscription(organizationId),
    );
  }, [organizationId, execute]);

  // ============================================================
  // LOAD HISTORY
  // ============================================================

  const loadHistory = useCallback(async () => {
    if (!organizationId) {
      setHistoryError("Organization ID is required.");

      return null;
    }

    try {
      setHistoryLoading(true);
      setHistoryError(null);

      const response =
        await organizationService.getSubscriptionHistory(organizationId);

      if (response?.success !== true) {
        const message = typeof response?.message === "string"
          ? response.message.trim()
          : "";
        throw new Error(message || "Unable to load subscription history.");
      }

      if (!Array.isArray(response.data)) {
        throw new Error(
          "Subscription history was not returned in the expected format.",
        );
      }

      const historyData = response.data;

      setHistory(historyData);
      setHistoryLoaded(true);
      setHistoryOrganizationId(organizationId);

      return historyData;
    } catch (error) {
      console.error("Failed to load subscription history:", error);

      setHistoryError(formatApiErrorMessage(error, {
        fallback: "Unable to load subscription history.",
      }));

      return null;
    } finally {
      setHistoryLoading(false);
    }
  }, [organizationId]);

  // ============================================================
  // CLEAR ACTION ERROR
  // ============================================================

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // ============================================================
  // CLEAR HISTORY ERROR
  // ============================================================

  const clearHistoryError = useCallback(() => {
    setHistoryError(null);
  }, []);

  return {
    // Actions
    loading,
    error,

    renew,
    changePlan,
    start,
    cancel,

    clearError,

    // History
    history,
    historyLoaded: historyLoaded && historyOrganizationId === organizationId,
    historyLoading,
    historyError,
    loadHistory,
    clearHistoryError,
  };
}
