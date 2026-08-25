// import { useCallback, useState } from "react";

// import organizationService from "../../services/organization/organization.service";

// export default function useOrganizationSubscription({
//   organizationId,
//   onSuccess,
// }) {
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState(null);

//   const execute = useCallback(
//     async (callback) => {
//       if (!organizationId) {
//         setError("Organization ID is required.");

//         return null;
//       }

//       if (loading) {
//         return null;
//       }

//       try {
//         setLoading(true);
//         setError(null);

//         const response = await callback();

//         if (!response?.success) {
//           throw new Error(response?.message || "Subscription action failed.");
//         }

//         await onSuccess?.(response);

//         return response;
//       } catch (error) {
//         console.error("Subscription action failed:", error);

//         const message =
//           error?.response?.data?.message ||
//           error?.message ||
//           "Subscription action failed.";

//         setError(message);

//         return null;
//       } finally {
//         setLoading(false);
//       }
//     },
//     [organizationId, loading, onSuccess],
//   );

//   const renew = useCallback(
//     async ({ billingCycle } = {}) => {
//       return execute(() =>
//         organizationService.renewSubscription(
//           organizationId,
//           billingCycle
//             ? {
//                 billing_cycle: billingCycle,
//               }
//             : {},
//         ),
//       );
//     },
//     [organizationId, execute],
//   );

//   const changePlan = useCallback(
//     async ({ plan, billingCycle }) => {
//       return execute(() =>
//         organizationService.changeSubscriptionPlan(organizationId, {
//           plan,
//           billing_cycle: billingCycle,
//         }),
//       );
//     },
//     [organizationId, execute],
//   );

//   const start = useCallback(
//     async ({ plan, billingCycle }) => {
//       return execute(() =>
//         organizationService.startSubscription(organizationId, {
//           plan,
//           billing_cycle: billingCycle,
//         }),
//       );
//     },
//     [organizationId, execute],
//   );

//   const cancel = useCallback(async () => {
//     return execute(() =>
//       organizationService.cancelSubscription(organizationId),
//     );
//   }, [organizationId, execute]);

//   const clearError = useCallback(() => {
//     setError(null);
//   }, []);

//   return {
//     loading,
//     error,

//     renew,
//     changePlan,
//     start,
//     cancel,

//     clearError,
//   };
// }
import { useCallback, useState } from "react";

import organizationService from "../../services/organization/organization.service";

export default function useOrganizationSubscription({
  organizationId,
  onSuccess,
}) {
  const [loading, setLoading] = useState(false);

  const [error, setError] = useState(null);

  // ============================================================
  // HISTORY STATE
  // ============================================================

  const [history, setHistory] = useState([]);

  const [historyLoading, setHistoryLoading] = useState(false);

  const [historyError, setHistoryError] = useState(null);

  // ============================================================
  // COMMON ACTION EXECUTOR
  // ============================================================

  const execute = useCallback(
    async (callback) => {
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
    [organizationId, loading, onSuccess],
  );

  // ============================================================
  // RENEW
  // ============================================================

  const renew = useCallback(
    async ({ billingCycle } = {}) => {
      return execute(() =>
        organizationService.renewSubscription(
          organizationId,
          billingCycle
            ? {
                billing_cycle: billingCycle,
              }
            : {},
        ),
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
      return execute(() =>
        organizationService.startSubscription(organizationId, {
          plan,
          billing_cycle: billingCycle,
        }),
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

      return [];
    }

    try {
      setHistoryLoading(true);
      setHistoryError(null);

      const response =
        await organizationService.getSubscriptionHistory(organizationId);

      if (!response?.success) {
        throw new Error(
          response?.message || "Unable to load subscription history.",
        );
      }

      const historyData = Array.isArray(response?.data) ? response.data : [];

      setHistory(historyData);

      return historyData;
    } catch (error) {
      console.error("Failed to load subscription history:", error);

      const message =
        error?.response?.data?.message ||
        error?.message ||
        "Unable to load subscription history.";

      setHistoryError(message);

      setHistory([]);

      return [];
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
    historyLoading,
    historyError,
    loadHistory,
    clearHistoryError,
  };
}
