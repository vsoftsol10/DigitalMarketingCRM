// import { Alert, Box, CircularProgress, Stack, Typography } from "@mui/material";
// import { useCallback, useEffect, useMemo, useState } from "react";

// import dmAutomationService from "../../services/dmAutomation.service";

// import DMAutomationHeader from "../../components/dm-automation/DMAutomationHeader";
// import DMAutomationInfoBanner from "../../components/dm-automation/DMAutomationInfoBanner";
// import DMAutomationGrid from "../../components/dm-automation/DMAutomationGrid";

// import { TYPOGRAPHY } from "../../theme/typography";
// import CreateAutomationDialog from "../../components/dm-automation/CreateAutomationDialog";
// export default function DMAutomation() {
//   const [automations, setAutomations] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);
//   const [createDialogOpen, setCreateDialogOpen] = useState(false);

//   const loadAutomations = useCallback(async () => {
//     try {
//       setLoading(true);
//       setError(null);

//       const response = await dmAutomationService.getAutomations();

//       if (!Array.isArray(response)) {
//         throw new Error("Invalid DM automation response.");
//       }

//       setAutomations(response);
//     } catch (error) {
//       console.error("Failed to load DM automations:", error);

//       setError(
//         error?.response?.data?.message ||
//           error?.message ||
//           "Unable to load DM automations.",
//       );
//     } finally {
//       setLoading(false);
//     }
//   }, []);

//   useEffect(() => {
//     loadAutomations();
//   }, [loadAutomations]);

//   const activeAutomationCount = useMemo(
//     () =>
//       automations.filter((automation) => automation.status === "active").length,
//     [automations],
//   );

//   const handleCreateAutomation = useCallback((automation) => {
//     setAutomations((currentAutomations) => [automation, ...currentAutomations]);

//     setCreateDialogOpen(false);
//   }, []);

//   const handleEditAutomation = (automation) => {
//     console.log("Edit automation:", automation);
//   };

//   const handleToggleStatus = (automation) => {
//     setAutomations((currentAutomations) =>
//       currentAutomations.map((item) =>
//         item.id === automation.id
//           ? {
//               ...item,
//               status: item.status === "active" ? "inactive" : "active",
//             }
//           : item,
//       ),
//     );
//   };

//   if (loading) {
//     return (
//       <Box
//         sx={{
//           minHeight: 400,
//           display: "flex",
//           alignItems: "center",
//           justifyContent: "center",
//         }}
//       >
//         <CircularProgress size={28} />
//       </Box>
//     );
//   }

//   if (error) {
//     return (
//       <Box sx={{ p: 3 }}>
//         <Alert severity="error">{error}</Alert>
//       </Box>
//     );
//   }

//   return (
//     <Box
//       sx={{
//         width: "100%",
//         minWidth: 0,
//       }}
//     >
//       <DMAutomationHeader
//         onCreateAutomation={() => setCreateDialogOpen(true)}
//       />

//       <DMAutomationInfoBanner activeCount={activeAutomationCount} />

//       <Box sx={{ mt: 3 }}>
//         {automations.length === 0 ? (
//           <Stack
//             alignItems="center"
//             justifyContent="center"
//             sx={{
//               minHeight: 300,
//               textAlign: "center",
//             }}
//           >
//             <Typography sx={TYPOGRAPHY.cardTitle}>
//               No automations available
//             </Typography>

//             <Typography sx={TYPOGRAPHY.bodySmall}>
//               Create your first DM automation to get started.
//             </Typography>
//           </Stack>
//         ) : (
//           <DMAutomationGrid
//             automations={automations}
//             onEdit={handleEditAutomation}
//             onToggleStatus={handleToggleStatus}
//           />
//         )}
//       </Box>
//       <CreateAutomationDialog
//         open={createDialogOpen}
//         onClose={() => setCreateDialogOpen(false)}
//         onSubmit={handleCreateAutomation}
//       />
//     </Box>
//   );
// }

import { Box } from "@mui/material";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import dmAutomationService from "../../services/dmAutomation.service";
import organizationService from "../../services/organization/organization.service";

import DMAutomationHeader from "../../components/dm-automation/DMAutomationHeader";
import LoadingState from "../../components/ui/LoadingState";
import ErrorState from "../../components/ui/ErrorState";
import EmptyState from "../../components/ui/EmptyState";
import OrganizationRequiredEmptyState from "../../components/organization/OrganizationRequiredEmptyState";
import DMAutomationInfoBanner from "../../components/dm-automation/DMAutomationInfoBanner";
import DMAutomationGrid from "../../components/dm-automation/DMAutomationGrid";
import CreateAutomationDialog from "../../components/dm-automation/CreateAutomationDialog";

export default function DMAutomation() {
  const organizationsQuery = useQuery({
    queryKey: ["organization-options", "dm-automation-empty-state"],
    queryFn: async () => {
      const response = await organizationService.getOrganizationOptions();
      const organizations = response?.data?.items;
      if (response?.success !== true || !Array.isArray(organizations)) {
        throw new Error("Organization data was not returned in the expected format.");
      }
      return organizations;
    },
  });

  const [automations, setAutomations] = useState([]);

  const [loading, setLoading] = useState(true);

  const [hasLoadedAutomations, setHasLoadedAutomations] = useState(false);

  const [loadError, setLoadError] = useState(null);

  const [mutationError, setMutationError] = useState(null);

  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const [creating, setCreating] = useState(false);

  const [editingAutomation, setEditingAutomation] = useState(null);

  const [updating, setUpdating] = useState(false);

  const loadAutomations = useCallback(async () => {
    try {
      setLoading(true);
      setLoadError(null);

      const response = await dmAutomationService.getAutomations();

      if (!Array.isArray(response)) {
        throw new Error("Invalid DM automation response.");
      }

      setAutomations(response);
      setHasLoadedAutomations(true);
    } catch (error) {
      console.error("Failed to load DM automations:", error);
      setLoadError(error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAutomations();
  }, [loadAutomations]);

  const activeAutomationCount = useMemo(
    () =>
      automations.filter((automation) => automation.status === "active").length,
    [automations],
  );

  const handleOpenCreateDialog = useCallback(() => {
    setMutationError(null);
    setCreateDialogOpen(true);
  }, []);

  const handleCloseCreateDialog = useCallback(() => {
    setCreateDialogOpen(false);
    setEditingAutomation(null);
    setMutationError(null);
  }, []);

  /**
   * Temporary UI-only create handler.
   *
   * Backend integration will be added later through
   * dmAutomationService.createAutomation().
   *
   * The dialog only returns a clean form payload.
   * This page does not know about the form implementation.
   */
  const handleCreateAutomation = useCallback(async (payload) => {
    try {
      setCreating(true);
      setMutationError(null);

      const createdAutomation =
        await dmAutomationService.createAutomation(payload);

      setAutomations((currentAutomations) => [
        createdAutomation,
        ...currentAutomations,
      ]);

      setCreateDialogOpen(false);
      setEditingAutomation(null);
    } catch (error) {
      console.error("Failed to create DM automation:", error);

      setMutationError(error);
    } finally {
      setCreating(false);
    }
  }, []);

  const handleUpdateAutomation = useCallback(
    async (payload) => {
      if (!editingAutomation?.id) {
        return;
      }

      try {
        setUpdating(true);
        setMutationError(null);

        const updatedAutomation = await dmAutomationService.updateAutomation(
          editingAutomation.id,
          payload,
        );

        setAutomations((currentAutomations) =>
          currentAutomations.map((automation) =>
            automation.id === editingAutomation.id
              ? updatedAutomation
              : automation,
          ),
        );

        setCreateDialogOpen(false);
        setEditingAutomation(null);
      } catch (error) {
        console.error("Failed to update DM automation:", error);

        setMutationError(error);
      } finally {
        setUpdating(false);
      }
    },
    [editingAutomation],
  );

  const handleEditAutomation = useCallback((automation) => {
    setMutationError(null);
    setEditingAutomation(automation);
    setCreateDialogOpen(true);
  }, []);

  const handleToggleStatus = useCallback(async (automation) => {
    const nextStatus = automation.status === "active" ? "inactive" : "active";

    try {
      setMutationError(null);

      const updatedAutomation =
        await dmAutomationService.toggleAutomationStatus(
          automation.id,
          nextStatus,
        );

      setAutomations((currentAutomations) =>
        currentAutomations.map((item) =>
          item.id === automation.id ? updatedAutomation : item,
        ),
      );
    } catch (error) {
      console.error("Failed to update DM automation status:", error);

      setMutationError(error);
    }
  }, []);

  if (organizationsQuery.isFetching) {
    return <LoadingState page="DM Automation" />;
  }

  if (
    organizationsQuery.isSuccess
    && Array.isArray(organizationsQuery.data)
    && organizationsQuery.data.length === 0
  ) {
    return <OrganizationRequiredEmptyState />;
  }

  if (loading && !hasLoadedAutomations) {
    return <LoadingState page="DM Automation" />;
  }

  if (!hasLoadedAutomations && loadError) {
    return (
      <ErrorState
        title="Unable to load DM automations"
        message={loadError}
        onRetry={loading ? undefined : loadAutomations}
        variant="page"
      />
    );
  }

  if (!hasLoadedAutomations) {
    return (
      <ErrorState
        title="Unable to load DM automations"
        message="Automation data was not returned."
        onRetry={loading ? undefined : loadAutomations}
        variant="page"
      />
    );
  }

  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,
      }}
    >
      {mutationError && (
        <ErrorState
          title="Unable to save automation changes"
          message={mutationError}
          variant="inline"
          sx={{
            position: "fixed",
            top: { xs: 12, sm: 20 },
            left: "50%",
            transform: "translateX(-50%)",
            width: "calc(100% - 24px)",
            maxWidth: 560,
            zIndex: (theme) => theme.zIndex.modal + 1,
          }}
        />
      )}

      <DMAutomationHeader onCreateAutomation={handleOpenCreateDialog} />

      <DMAutomationInfoBanner activeCount={activeAutomationCount} />

      <Box sx={{ mt: 3 }}>
        {automations.length === 0 ? (
          <EmptyState
            title="No automations available"
            description="Create your first DM automation to get started."
            sx={{ minHeight: 300 }}
          />
        ) : (
          <DMAutomationGrid
            automations={automations}
            onEdit={handleEditAutomation}
            onToggleStatus={handleToggleStatus}
          />
        )}
      </Box>

      <CreateAutomationDialog
        open={createDialogOpen}
        onClose={handleCloseCreateDialog}
        onSubmit={
          editingAutomation ? handleUpdateAutomation : handleCreateAutomation
        }
        submitting={creating || updating}
        initialData={editingAutomation}
      />
    </Box>
  );
}
