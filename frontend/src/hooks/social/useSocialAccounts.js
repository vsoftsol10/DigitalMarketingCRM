// import { useCallback, useEffect, useState } from "react";

// import socialAccountService from "../../services/social/socialAccount.service";

// export default function useSocialAccounts(
//   organizationId,
//   { enabled = true } = {},
// ) {
//   const [accounts, setAccounts] = useState([]);
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState(null);

//   // ============================================================
//   // FETCH ACCOUNTS
//   // ============================================================

//   const fetchAccounts = useCallback(async () => {
//     if (!organizationId || !enabled) {
//       setAccounts([]);
//       return;
//     }

//     try {
//       setLoading(true);
//       setError(null);

//       const response =
//         await socialAccountService.getOrganizationSocialAccounts(
//           organizationId,
//         );

//       if (!response?.success) {
//         throw new Error(response?.message || "Unable to load social accounts.");
//       }

//       const accountsData = Array.isArray(response.data) ? response.data : [];

//       setAccounts(accountsData);
//     } catch (error) {
//       console.error("Failed to load social accounts:", error);

//       setError(
//         error?.response?.data?.message ||
//           error?.message ||
//           "Unable to load social accounts.",
//       );

//       setAccounts([]);
//     } finally {
//       setLoading(false);
//     }
//   }, [organizationId, enabled]);

//   // ============================================================
//   // INITIAL LOAD
//   // ============================================================

//   useEffect(() => {
//     fetchAccounts();
//   }, [fetchAccounts]);

//   // ============================================================
//   // REFRESH
//   // ============================================================

//   const refresh = useCallback(() => {
//     return fetchAccounts();
//   }, [fetchAccounts]);

//   // ============================================================
//   // UPDATE
//   // ============================================================

//   const updateAccount = useCallback(
//     async (socialAccountId, payload) => {
//       if (!organizationId) {
//         throw new Error("Organization ID is required.");
//       }

//       try {
//         setError(null);

//         const response = await socialAccountService.updateSocialAccount(
//           organizationId,
//           socialAccountId,
//           payload,
//         );

//         if (!response?.success) {
//           throw new Error(
//             response?.message || "Unable to update social account.",
//           );
//         }

//         await refresh();

//         return response;
//       } catch (error) {
//         console.error("Failed to update social account:", error);

//         const message =
//           error?.response?.data?.message ||
//           error?.message ||
//           "Unable to update social account.";

//         setError(message);

//         throw error;
//       }
//     },
//     [organizationId, refresh],
//   );

//   // ============================================================
//   // DELETE
//   // ============================================================

//   const deleteAccount = useCallback(
//     async (socialAccountId) => {
//       if (!organizationId) {
//         throw new Error("Organization ID is required.");
//       }

//       try {
//         setError(null);

//         const response = await socialAccountService.deleteSocialAccount(
//           organizationId,
//           socialAccountId,
//         );

//         if (!response?.success) {
//           throw new Error(
//             response?.message || "Unable to delete social account.",
//           );
//         }

//         await refresh();

//         return response;
//       } catch (error) {
//         console.error("Failed to delete social account:", error);

//         const message =
//           error?.response?.data?.message ||
//           error?.message ||
//           "Unable to delete social account.";

//         setError(message);

//         throw error;
//       }
//     },
//     [organizationId, refresh],
//   );

//   return {
//     accounts,
//     loading,
//     error,
//     refresh,
//     updateAccount,
//     deleteAccount,
//   };
// }

import { useCallback, useEffect, useRef, useState } from "react";

import socialAccountService from "../../services/social/socialAccount.service";

export default function useSocialAccounts(
  organizationId,
  { enabled = true } = {},
) {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const requestRef = useRef({ id: 0, controller: null });

  // ============================================================
  // FETCH ACCOUNTS
  // ============================================================

  const fetchAccounts = useCallback(async () => {
    if (!organizationId || !enabled) {
      requestRef.current.controller?.abort();
      requestRef.current = {
        id: requestRef.current.id + 1,
        controller: null,
      };
      setAccounts([]);
      setLoading(false);
      return;
    }

    requestRef.current.controller?.abort();
    const requestId = requestRef.current.id + 1;
    const controller = new AbortController();
    requestRef.current = { id: requestId, controller };

    try {
      setLoading(true);
      setError(null);

      const response =
        await socialAccountService.getOrganizationSocialAccounts(
          organizationId,
          { signal: controller.signal },
        );

      if (requestRef.current.id !== requestId) {
        return;
      }

      if (!response?.success) {
        throw new Error(response?.message || "Unable to load social accounts.");
      }

      const accountsData = Array.isArray(response.data) ? response.data : [];

      setAccounts(accountsData);
    } catch (error) {
      if (controller.signal.aborted || requestRef.current.id !== requestId) {
        return;
      }

      console.error("Failed to load social accounts:", error);

      setError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to load social accounts.",
      );

      setAccounts([]);
    } finally {
      if (requestRef.current.id === requestId) {
        requestRef.current = { id: requestId, controller: null };
        setLoading(false);
      }
    }
  }, [organizationId, enabled]);

  // ============================================================
  // INITIAL LOAD
  // ============================================================

  useEffect(() => {
    fetchAccounts();

    return () => {
      const activeRequest = requestRef.current;
      activeRequest.controller?.abort();
      requestRef.current = { id: activeRequest.id + 1, controller: null };
    };
  }, [fetchAccounts]);

  // ============================================================
  // REFRESH
  // ============================================================

  const refresh = useCallback(() => {
    return fetchAccounts();
  }, [fetchAccounts]);

  // ============================================================
  // UPDATE
  // ============================================================

  const updateAccount = useCallback(
    async (socialAccountId, payload) => {
      if (!organizationId) {
        throw new Error("Organization ID is required.");
      }

      if (!socialAccountId) {
        throw new Error("Social account ID is required.");
      }

      try {
        setError(null);

        const response = await socialAccountService.updateSocialAccount(
          organizationId,
          socialAccountId,
          payload,
        );

        if (!response?.success) {
          throw new Error(
            response?.message || "Unable to update social account.",
          );
        }

        await refresh();

        return response;
      } catch (error) {
        console.error("Failed to update social account:", error);

        const message =
          error?.response?.data?.message ||
          error?.message ||
          "Unable to update social account.";

        setError(message);

        throw error;
      }
    },
    [organizationId, refresh],
  );

  // ============================================================
  // DISCONNECT
  // ============================================================

  const disconnectAccount = useCallback(
    async (socialAccountId) => {
      if (!organizationId) {
        throw new Error("Organization ID is required.");
      }

      if (!socialAccountId) {
        throw new Error("Social account ID is required.");
      }

      try {
        setError(null);

        const response = await socialAccountService.disconnectSocialAccount(
          organizationId,
          socialAccountId,
        );

        if (!response?.success) {
          throw new Error(
            response?.message || "Unable to disconnect social account.",
          );
        }

        await refresh();

        return response;
      } catch (error) {
        console.error("Failed to disconnect social account:", error);

        const message =
          error?.response?.data?.message ||
          error?.message ||
          "Unable to disconnect social account.";

        setError(message);

        throw error;
      }
    },
    [organizationId, refresh],
  );

  // ============================================================
  // DELETE
  // ============================================================

  const deleteAccount = useCallback(
    async (socialAccountId) => {
      if (!organizationId) {
        throw new Error("Organization ID is required.");
      }

      if (!socialAccountId) {
        throw new Error("Social account ID is required.");
      }

      try {
        setError(null);

        const response = await socialAccountService.deleteSocialAccount(
          organizationId,
          socialAccountId,
        );

        if (!response?.success) {
          throw new Error(
            response?.message || "Unable to delete social account.",
          );
        }

        await refresh();

        return response;
      } catch (error) {
        console.error("Failed to delete social account:", error);

        const message =
          error?.response?.data?.message ||
          error?.message ||
          "Unable to delete social account.";

        setError(message);

        throw error;
      }
    },
    [organizationId, refresh],
  );

  // ============================================================
  // RETURN
  // ============================================================

  return {
    accounts,
    loading,
    error,
    refresh,
    updateAccount,
    disconnectAccount,
    deleteAccount,
  };
}
