// import { Box } from "@mui/material";
// import { useEffect, useState } from "react";
// import { useNavigate } from "react-router-dom";

// import contentPlannerService from "../../services/contentPlanner.service";

// import ContentPlannerHeader from "../../components/planner/ContentPlannerHeader";
// import ContentPlannerStats from "../../components/planner/ContentPlannerStats";
// import ContentPlannerFilters from "../../components/planner/ContentPlannerFilters";
// import ContentPlannerTable from "../../components/planner/ContentPlannerTable";
// import ConfirmDialog from "../../components/ui/dialog/ConfirmDialog";

// export default function ContentPlanner() {
//   const navigate = useNavigate();

//   const [planner, setPlanner] = useState(null);
//   const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

//   const [selectedIdea, setSelectedIdea] = useState(null);

//   const [filters, setFilters] = useState({
//     search: "",
//     organization: "all",
//   });

//   useEffect(() => {
//     loadPlanner();
//   }, []);

//   async function loadPlanner() {
//     const response = await contentPlannerService.getContentPlanner();

//     setPlanner(response);
//   }

//   function handleSearchChange(search) {
//     setFilters((prev) => ({
//       ...prev,
//       search,
//     }));
//   }

//   function handleOrganizationChange(organization) {
//     setFilters((prev) => ({
//       ...prev,
//       organization,
//     }));
//   }

//   function handleOpenDeleteDialog(idea) {
//     setSelectedIdea(idea);
//     setDeleteDialogOpen(true);
//   }

//   function handleCloseDeleteDialog() {
//     setDeleteDialogOpen(false);
//     setSelectedIdea(null);
//   }

//   async function handleDeleteIdea() {
//     if (!selectedIdea) return;

//     await contentPlannerService.deleteIdea(selectedIdea.id);

//     await loadPlanner();

//     handleCloseDeleteDialog();
//   }

//   if (!planner) {
//     return null;
//   }

//   return (
//     <>
//       <ContentPlannerHeader
//         onMonthlyPlan={() => console.log("Monthly Plan")}
//         onCreateIdea={() => navigate("/planner/new")}
//       />

//       <Box sx={{ mt: 4 }}>
//         <ContentPlannerStats statistics={planner.statistics} />
//       </Box>

//       <ContentPlannerFilters
//         organizations={planner.organizations}
//         filters={filters}
//         onSearchChange={handleSearchChange}
//         onOrganizationChange={handleOrganizationChange}
//       />

//       <Box sx={{ mt: 4 }}>
//         <ContentPlannerTable
//           ideas={planner.ideas}
//           onDelete={handleOpenDeleteDialog}
//         />
//       </Box>
//       <ConfirmDialog
//         open={deleteDialogOpen}
//         title="Delete Content Idea"
//         message="Are you sure you want to delete"
//         entityName={selectedIdea?.title}
//         description="This action cannot be undone."
//         confirmText="Delete"
//         loading={false}
//         onClose={handleCloseDeleteDialog}
//         onConfirm={handleDeleteIdea}
//       />
//     </>
//   );
// }

import { Alert, Box, CircularProgress } from "@mui/material";

import { useCallback, useEffect, useRef, useState } from "react";

import { useNavigate } from "react-router-dom";

import contentPlannerService from "../../services/contentPlanner.service";

import ContentPlannerHeader from "../../components/planner/ContentPlannerHeader";
import ContentPlannerStats from "../../components/planner/ContentPlannerStats";
import ContentPlannerFilters from "../../components/planner/ContentPlannerFilters";
import ContentPlannerTable from "../../components/planner/ContentPlannerTable";
import ConfirmDialog from "../../components/ui/dialog/ConfirmDialog";

import useDebounce from "../../hooks/common/useDebounce";

const DEFAULT_FILTERS = {
  search: "",
  organization: "all",
};

export default function ContentPlanner() {
  const navigate = useNavigate();

  // ============================================================
  // PLANNER STATE
  // ============================================================

  const [planner, setPlanner] = useState(null);

  const [initialLoading, setInitialLoading] = useState(true);

  const [tableLoading, setTableLoading] = useState(false);

  const [error, setError] = useState(null);

  // ============================================================
  // FILTER STATE
  // ============================================================

  const [filters, setFilters] = useState(DEFAULT_FILTERS);

  const debouncedSearch = useDebounce(filters.search, 400);

  const hasMountedFilterEffect = useRef(false);

  // ============================================================
  // DELETE STATE
  // ============================================================

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const [deleteLoading, setDeleteLoading] = useState(false);

  const [selectedIdea, setSelectedIdea] = useState(null);

  // ============================================================
  // LOAD CONTENT PLANNER
  // ============================================================

  const loadPlanner = useCallback(
    async ({ search = "", organization = "all", initial = false } = {}) => {
      try {
        if (initial) {
          setInitialLoading(true);
        } else {
          setTableLoading(true);
        }

        setError(null);

        const response = await contentPlannerService.getContentPlanner({
          search,
          organization,
        });

        if (!response?.success) {
          throw new Error(
            response?.message || "Unable to load content planner.",
          );
        }

        if (!response?.data) {
          throw new Error("Content planner data was not returned.");
        }

        setPlanner(response.data);
      } catch (error) {
        console.error("Failed to load content planner:", error);

        setError(
          error?.response?.data?.message ||
            error?.message ||
            "Unable to load content planner.",
        );
      } finally {
        setInitialLoading(false);
        setTableLoading(false);
      }
    },
    [],
  );

  // ============================================================
  // INITIAL PAGE LOAD
  // ============================================================

  useEffect(() => {
    loadPlanner({
      search: "",
      organization: "all",
      initial: true,
    });
  }, [loadPlanner]);

  // ============================================================
  // SEARCH / FILTER LOAD
  // ============================================================

  useEffect(() => {
    /*
     * Skip the first render because the initial loader above
     * already performs the initial request.
     */
    if (!hasMountedFilterEffect.current) {
      hasMountedFilterEffect.current = true;
      return;
    }

    loadPlanner({
      search: debouncedSearch.trim(),
      organization: filters.organization,
      initial: false,
    });
  }, [debouncedSearch, filters.organization, loadPlanner]);

  // ============================================================
  // SEARCH
  // ============================================================

  const handleSearchChange = useCallback((search) => {
    setFilters((previous) => ({
      ...previous,
      search,
    }));
  }, []);

  // ============================================================
  // ORGANIZATION FILTER
  // ============================================================

  const handleOrganizationChange = useCallback((organization) => {
    setFilters((previous) => ({
      ...previous,
      organization,
    }));
  }, []);

  // ============================================================
  // CLEAR FILTERS
  // ============================================================

  const handleClearFilters = useCallback(() => {
    setFilters({
      ...DEFAULT_FILTERS,
    });
  }, []);

  // ============================================================
  // DELETE DIALOG
  // ============================================================

  const handleOpenDeleteDialog = useCallback((idea) => {
    setSelectedIdea(idea);
    setDeleteDialogOpen(true);
  }, []);

  const handleCloseDeleteDialog = useCallback(() => {
    if (deleteLoading) {
      return;
    }

    setDeleteDialogOpen(false);
    setSelectedIdea(null);
  }, [deleteLoading]);

  // ============================================================
  // DELETE IDEA
  // ============================================================

  const handleDeleteIdea = useCallback(async () => {
    if (!selectedIdea?.id || deleteLoading) {
      return;
    }

    try {
      setDeleteLoading(true);
      setError(null);

      const response = await contentPlannerService.deleteIdea(selectedIdea.id);

      if (!response?.success) {
        throw new Error(response?.message || "Unable to delete content idea.");
      }

      /*
       * Reload using the currently applied filters.
       * This keeps the table state consistent after deletion.
       */
      await loadPlanner({
        search: debouncedSearch.trim(),
        organization: filters.organization,
        initial: false,
      });

      setDeleteDialogOpen(false);
      setSelectedIdea(null);
    } catch (error) {
      console.error("Failed to delete content idea:", error);

      setError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to delete content idea.",
      );
    } finally {
      setDeleteLoading(false);
    }
  }, [
    selectedIdea,
    deleteLoading,
    loadPlanner,
    debouncedSearch,
    filters.organization,
  ]);

  // ============================================================
  // INITIAL PAGE LOADING
  // ============================================================

  if (initialLoading && !planner) {
    return (
      <Box
        sx={{
          minHeight: 500,

          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <CircularProgress size={30} />
      </Box>
    );
  }

  // ============================================================
  // INITIAL ERROR
  // ============================================================

  if (error && !planner) {
    return (
      <Box
        sx={{
          p: 3,
        }}
      >
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  // ============================================================
  // SAFE DATA
  // ============================================================

  const statistics = planner?.statistics || {};

  const organizations = planner?.organizations || [];

  const ideas = planner?.ideas || [];

  const hasActiveFilters =
    filters.search.trim() !== "" || filters.organization !== "all";

  return (
    <>
      {/* =======================================================
          PAGE ERROR
      ======================================================= */}

      {error && (
        <Alert
          severity="error"
          sx={{
            mb: 3,
            borderRadius: "12px",
          }}
        >
          {error}
        </Alert>
      )}

      {/* =======================================================
          HEADER
      ======================================================= */}

      <ContentPlannerHeader
        onMonthlyPlan={() => {
          console.log("Monthly Plan");
        }}
        onCreateIdea={() => navigate("/planner/new")}
      />

      {/* =======================================================
          STATS
      ======================================================= */}

      <Box sx={{ mt: 4 }}>
        <ContentPlannerStats statistics={statistics} />
      </Box>

      {/* =======================================================
          FILTERS
      ======================================================= */}

      <ContentPlannerFilters
        organizations={organizations}
        filters={filters}
        onSearchChange={handleSearchChange}
        onOrganizationChange={handleOrganizationChange}
        onClearFilters={handleClearFilters}
        hasActiveFilters={hasActiveFilters}
      />

      {/* =======================================================
          TABLE
      ======================================================= */}

      <Box sx={{ mt: 4 }}>
        <ContentPlannerTable
          ideas={ideas}
          onDelete={handleOpenDeleteDialog}
          loading={tableLoading}
          hasActiveFilters={hasActiveFilters}
        />
      </Box>

      {/* =======================================================
          DELETE CONFIRMATION
      ======================================================= */}

      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete Content Idea"
        message="Are you sure you want to delete"
        entityName={selectedIdea?.title}
        description="This action cannot be undone."
        confirmText="Delete"
        loading={deleteLoading}
        onClose={handleCloseDeleteDialog}
        onConfirm={handleDeleteIdea}
      />
    </>
  );
}
