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

import { Alert, Box, CircularProgress, Stack, Typography } from "@mui/material";

import { useCallback, useEffect, useMemo, useState } from "react";

import dmAutomationService from "../../services/dmAutomation.service";

import DMAutomationHeader from "../../components/dm-automation/DMAutomationHeader";
import DMAutomationInfoBanner from "../../components/dm-automation/DMAutomationInfoBanner";
import DMAutomationGrid from "../../components/dm-automation/DMAutomationGrid";
import CreateAutomationDialog from "../../components/dm-automation/CreateAutomationDialog";

import { TYPOGRAPHY } from "../../theme/typography";

export default function DMAutomation() {
  const [automations, setAutomations] = useState([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState(null);

  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const [creating, setCreating] = useState(false);

  const [editingAutomation, setEditingAutomation] = useState(null);

  const [updating, setUpdating] = useState(false);

  const loadAutomations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await dmAutomationService.getAutomations();

      if (!Array.isArray(response)) {
        throw new Error("Invalid DM automation response.");
      }

      setAutomations(response);
    } catch (error) {
      console.error("Failed to load DM automations:", error);

      setError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to load DM automations.",
      );
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
    setCreateDialogOpen(true);
  }, []);

  const handleCloseCreateDialog = useCallback(() => {
    setCreateDialogOpen(false);
    setEditingAutomation(null);
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
      setError(null);

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

      setError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to create DM automation.",
      );
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
        setError(null);

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

        setError(
          error?.response?.data?.message ||
            error?.message ||
            "Unable to update DM automation.",
        );
      } finally {
        setUpdating(false);
      }
    },
    [editingAutomation],
  );

  const handleEditAutomation = useCallback((automation) => {
    setEditingAutomation(automation);
    setCreateDialogOpen(true);
  }, []);

  const handleToggleStatus = useCallback(async (automation) => {
    const nextStatus = automation.status === "active" ? "inactive" : "active";

    try {
      setError(null);

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

      setError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to update automation status.",
      );
    }
  }, []);

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
        <Alert severity="error">{error}</Alert>
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
      <DMAutomationHeader onCreateAutomation={handleOpenCreateDialog} />

      <DMAutomationInfoBanner activeCount={activeAutomationCount} />

      <Box sx={{ mt: 3 }}>
        {automations.length === 0 ? (
          <Stack
            alignItems="center"
            justifyContent="center"
            sx={{
              minHeight: 300,
              textAlign: "center",
            }}
          >
            <Typography sx={TYPOGRAPHY.cardTitle}>
              No automations available
            </Typography>

            <Typography sx={TYPOGRAPHY.bodySmall}>
              Create your first DM automation to get started.
            </Typography>
          </Stack>
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
