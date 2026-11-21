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

import { Alert, Box } from "@mui/material";

import { useCallback, useEffect, useRef, useState } from "react";

import { useNavigate } from "react-router-dom";
import LightbulbOutlinedIcon from "@mui/icons-material/LightbulbOutlined";

import contentPlannerService from "../../services/contentPlanner.service";

import ContentPlannerHeader from "../../components/planner/ContentPlannerHeader";
import ContentPlannerStats from "../../components/planner/ContentPlannerStats";
import ContentPlannerFilters from "../../components/planner/ContentPlannerFilters";
import ContentPlannerTable from "../../components/planner/ContentPlannerTable";
import ContentPlannerPostDetailsDialog from "../../components/planner/ContentPlannerPostDetailsDialog";
import OrganizationRequiredEmptyState from "../../components/organization/OrganizationRequiredEmptyState";
import ConfirmDialog from "../../components/ui/dialog/ConfirmDialog";
import PlannerLoadingState from "../../components/planner/PlannerLoadingState";
import PlannerErrorState from "../../components/planner/PlannerErrorState";
import PlannerEmptyState from "../../components/planner/PlannerEmptyState";
import { formatApiErrorMessage } from "../../utils/apiErrorMessage";

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

  const [loadError, setLoadError] = useState(null);
  const [actionError, setActionError] = useState(null);

  // ============================================================
  // FILTER STATE
  // ============================================================

  const [filters, setFilters] = useState(DEFAULT_FILTERS);

  const debouncedSearch = useDebounce(filters.search, 400);

  const initialFilterKey = JSON.stringify({
    search: debouncedSearch.trim(),
    organization: filters.organization,
  });
  const lastFilterKeyRef = useRef(initialFilterKey);
  const plannerRequestId = useRef(0);

  useEffect(() => () => {
    plannerRequestId.current += 1;
  }, []);

  // ============================================================
  // DELETE STATE
  // ============================================================

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const [deleteLoading, setDeleteLoading] = useState(false);

  const [selectedIdea, setSelectedIdea] = useState(null);

  const [selectedViewItem, setSelectedViewItem] = useState(null);

  // ============================================================
  // LOAD CONTENT PLANNER
  // ============================================================

  const loadPlanner = useCallback(
    async ({ search = "", organization = "all", initial = false } = {}) => {
      const requestId = plannerRequestId.current + 1;
      plannerRequestId.current = requestId;

      try {
        if (initial) {
          setInitialLoading(true);
        } else {
          setTableLoading(true);
        }

        setLoadError(null);

        const response = await contentPlannerService.getContentPlanner({
          search,
          organization,
        });

        if (requestId !== plannerRequestId.current) {
          return;
        }

        if (!response?.success) {
          throw new Error(
            response?.message || "Unable to load content planner.",
          );
        }

        if (!response?.data) {
          throw new Error("Content planner data was not returned.");
        }

        if (!Array.isArray(response.data.ideas) || !Array.isArray(response.data.organizations)) {
          throw new Error("Content planner data was incomplete.");
        }

        setPlanner(response.data);
      } catch (error) {
        if (requestId !== plannerRequestId.current) {
          return;
        }

        console.error("Failed to load content planner:", error);

        setLoadError(formatApiErrorMessage(error, {
          fallback: "Unable to load content planner.",
        }));
      } finally {
        if (requestId === plannerRequestId.current) {
          setInitialLoading(false);
          setTableLoading(false);
        }
      }
    },
    [],
  );

  // ============================================================
  // INITIAL PAGE LOAD
  // ============================================================

  useEffect(() => {
    let active = true;
    Promise.resolve().then(() => {
      if (!active) return;

      loadPlanner({
        search: "",
        organization: "all",
        initial: true,
      });
    });

    return () => {
      active = false;
    };
  }, [loadPlanner]);

  // ============================================================
  // SEARCH / FILTER LOAD
  // ============================================================

  useEffect(() => {
    const filterKey = JSON.stringify({
      search: debouncedSearch.trim(),
      organization: filters.organization,
    });

    if (lastFilterKeyRef.current === filterKey) {
      return;
    }

    lastFilterKeyRef.current = filterKey;

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

  const handleViewIdea = useCallback((idea) => {
    setSelectedViewItem(idea);
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
      setActionError(null);

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

      setActionError(formatApiErrorMessage(error, {
        fallback: "Unable to delete content idea.",
      }));
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

  // ============================================================
  // INITIAL ERROR
  // ============================================================

  if (initialLoading && !planner) {
    return <PlannerLoadingState page="Content Planner" />;
  }

  if (loadError && !planner) {
    return <PlannerErrorState message={loadError} onRetry={() => loadPlanner({
      search: debouncedSearch.trim(),
      organization: filters.organization,
      initial: true,
    })} variant="page" />;
  }

  // ============================================================
  // SAFE DATA
  // ============================================================

  const statistics = planner?.statistics || {};

  const organizations = planner?.organizations || [];

  if (
    planner
    && !initialLoading
    && !tableLoading
    && !loadError
    && Array.isArray(planner.organizations)
    && planner.organizations.length === 0
  ) {
    return <OrganizationRequiredEmptyState onAction={() => navigate("/organizations/new")} />;
  }

  const ideas = planner?.ideas || [];
  const isPlannerLoading = (initialLoading && !planner) || tableLoading;

  const hasActiveFilters =
    filters.search.trim() !== "" || filters.organization !== "all";

  return (
    <>
      {/* =======================================================
          PAGE ERROR
      ======================================================= */}

      {loadError && (
        <PlannerErrorState
          message={loadError}
          onRetry={() => loadPlanner({
            search: debouncedSearch.trim(),
            organization: filters.organization,
            initial: false,
          })}
          variant="inline"
        />
      )}
      {actionError && <Alert severity="error" sx={{ mb: 3, borderRadius: "12px", border: "1px solid #FECACA" }}>{actionError}</Alert>}

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
        {isPlannerLoading ? (
          <ContentPlannerTable
            ideas={ideas}
            onDelete={handleOpenDeleteDialog}
            onView={handleViewIdea}
            loading
            hasActiveFilters={hasActiveFilters}
          />
        ) : !loadError && ideas.length === 0 ? (
          <PlannerEmptyState
            icon={<LightbulbOutlinedIcon />}
            title={hasActiveFilters ? "No matching content ideas" : "No content ideas yet"}
            description={hasActiveFilters
              ? "Try changing your search or organization filter."
              : "Create a content idea to start planning your content."}
            actionLabel={hasActiveFilters ? "Clear filters" : "Create content idea"}
            onAction={hasActiveFilters ? handleClearFilters : () => navigate("/planner/new")}
            sx={{ minHeight: 240 }}
          />
        ) : (
          <ContentPlannerTable
            ideas={ideas}
            onDelete={handleOpenDeleteDialog}
            onView={handleViewIdea}
            loading={false}
            hasActiveFilters={hasActiveFilters}
          />
        )}
      </Box>

      {/* =======================================================
          DELETE CONFIRMATION
      ======================================================= */}

      <ConfirmDialog
        crmStyle
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

      <ContentPlannerPostDetailsDialog
        open={Boolean(selectedViewItem)}
        idea={selectedViewItem}
        onClose={() => setSelectedViewItem(null)}
      />
    </>
  );
}
