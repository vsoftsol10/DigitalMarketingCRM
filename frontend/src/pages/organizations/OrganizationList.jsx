// import { Alert, Box, CircularProgress, Stack, Typography } from "@mui/material";

// import { useCallback, useEffect, useMemo, useRef, useState } from "react";

// import DashboardOutlinedIcon from "@mui/icons-material/DashboardOutlined";
// import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
// import TrendingUpOutlinedIcon from "@mui/icons-material/TrendingUpOutlined";
// import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
// import CampaignOutlinedIcon from "@mui/icons-material/CampaignOutlined";

// import { useNavigate } from "react-router-dom";

// import Breadcrumb from "../../components/organization/list/Breadcrumb";
// import Header from "../../components/organization/list/Header";
// import StatsCards from "../../components/organization/list/StatsCards";
// import SearchTabs from "../../components/organization/list/SearchTabs";
// import OrganizationGrid from "../../components/organization/list/OrganizationGrid";

// import organizationService from "../../services/organization/organization.service";

// export default function OrganizationList() {
//   const navigate = useNavigate();

//   // ============================================================
//   // ORGANIZATION DATA
//   // ============================================================

//   const [organizations, setOrganizations] = useState([]);

//   // ============================================================
//   // SEARCH / FILTER STATE
//   // ============================================================

//   const [searchInput, setSearchInput] = useState("");

//   const [search, setSearch] = useState("");

//   const [activeTab, setActiveTab] = useState("all");

//   // ============================================================
//   // LOADING STATE
//   // ============================================================

//   const [initialLoading, setInitialLoading] = useState(true);

//   const [refreshing, setRefreshing] = useState(false);

//   // ============================================================
//   // ERROR STATE
//   // ============================================================

//   const [error, setError] = useState(null);

//   // ============================================================
//   // GLOBAL SUMMARY
//   // ============================================================

//   const [summary, setSummary] = useState({
//     total_clients: 0,
//     active_organizations: 0,
//     inactive_organizations: 0,
//     connected_accounts: 0,
//     active_subscriptions: 0,
//   });

//   // ============================================================
//   // INITIAL REQUEST TRACKING
//   // ============================================================

//   const isFirstLoad = useRef(true);

//   // ============================================================
//   // SEARCH DEBOUNCE
//   // ============================================================

//   useEffect(() => {
//     const timer = window.setTimeout(() => {
//       setSearch(searchInput.trim());
//     }, 400);

//     return () => {
//       window.clearTimeout(timer);
//     };
//   }, [searchInput]);

//   // ============================================================
//   // BREADCRUMB
//   // ============================================================

//   const breadcrumbItems = useMemo(
//     () => [
//       {
//         label: "Dashboard",
//         icon: DashboardOutlinedIcon,
//         path: "/",
//       },
//       {
//         label: "Organizations",
//       },
//     ],
//     [],
//   );

//   // ============================================================
//   // LOAD ORGANIZATIONS
//   // ============================================================

//   const loadOrganizations = useCallback(async () => {
//     try {
//       setError(null);

//       if (isFirstLoad.current) {
//         setInitialLoading(true);
//       } else {
//         setRefreshing(true);
//       }

//       const status =
//         activeTab === "active"
//           ? "ACTIVE"
//           : activeTab === "inactive"
//             ? "INACTIVE"
//             : "";

//       const response = await organizationService.getOrganizations({
//         search,
//         status,
//         page: 1,
//         pageSize: 10,
//         ordering: "-created_at",
//       });

//       if (!response?.success) {
//         throw new Error(response?.message || "Unable to load organizations.");
//       }

//       const responseData = response?.data;

//       const nextOrganizations = Array.isArray(responseData?.items)
//         ? responseData.items
//         : [];

//       const nextSummary = responseData?.summary || {
//         total_clients: 0,
//         active_organizations: 0,
//         inactive_organizations: 0,
//         connected_accounts: 0,
//         active_subscriptions: 0,
//       };

//       setOrganizations(nextOrganizations);

//       setSummary(nextSummary);
//     } catch (error) {
//       console.error("Failed to load organizations:", error);

//       const errorMessage =
//         error?.response?.data?.message ||
//         error?.message ||
//         "Unable to load organizations.";

//       setError(errorMessage);

//       /*
//        * During background refresh we intentionally keep the
//        * existing organizations and summary on screen.
//        */
//       if (isFirstLoad.current) {
//         setOrganizations([]);

//         setSummary({
//           total_clients: 0,
//           active_organizations: 0,
//           inactive_organizations: 0,
//           connected_accounts: 0,
//           active_subscriptions: 0,
//         });
//       }
//     } finally {
//       setInitialLoading(false);
//       setRefreshing(false);

//       isFirstLoad.current = false;
//     }
//   }, [activeTab, search]);

//   // ============================================================
//   // FETCH DATA
//   // ============================================================

//   useEffect(() => {
//     loadOrganizations();
//   }, [loadOrganizations]);

//   // ============================================================
//   // TAB COUNTS
//   //
//   // Always use global summary values.
//   // Search/filter must not change the counts.
//   // ============================================================

//   const counts = useMemo(
//     () => ({
//       all: summary.total_clients || 0,

//       active: summary.active_organizations || 0,

//       inactive: summary.inactive_organizations || 0,
//     }),
//     [
//       summary.total_clients,
//       summary.active_organizations,
//       summary.inactive_organizations,
//     ],
//   );

//   // ============================================================
//   // STATISTICS
//   // ============================================================

//   const statistics = useMemo(
//     () => [
//       {
//         title: "TOTAL CLIENTS",
//         value: summary.total_clients || 0,
//         icon: BusinessOutlinedIcon,
//       },
//       {
//         title: "ACTIVE ORGANIZATIONS",
//         value: summary.active_organizations || 0,
//         icon: TrendingUpOutlinedIcon,
//       },
//       {
//         title: "CONNECTED ACCOUNTS",
//         value: summary.connected_accounts || 0,
//         icon: GroupsOutlinedIcon,
//       },
//       {
//         title: "ACTIVE SUBSCRIPTIONS",
//         value: summary.active_subscriptions || 0,
//         icon: CampaignOutlinedIcon,
//       },
//     ],
//     [summary],
//   );

//   // ============================================================
//   // TAB CHANGE
//   // ============================================================

//   const handleTabChange = useCallback((tab) => {
//     setActiveTab(tab);
//   }, []);

//   // ============================================================
//   // SEARCH CHANGE
//   // ============================================================

//   const handleSearchChange = useCallback((value) => {
//     setSearchInput(value);
//   }, []);

//   // ============================================================
//   // CLEAR SEARCH
//   //
//   // SearchTabs currently owns the search field.
//   // Clearing search means setting it to empty.
//   // ============================================================

//   const handleClearSearch = useCallback(() => {
//     setSearchInput("");
//   }, []);

//   // ============================================================
//   // ORGANIZATION CLICK
//   // ============================================================

//   const handleOrganizationClick = useCallback(
//     (organization) => {
//       const organizationId = organization?.organization_id;

//       if (!organizationId) {
//         return;
//       }

//       navigate(`/organizations/${organizationId}/overview`);
//     },
//     [navigate],
//   );

//   // ============================================================
//   // FILTER STATE
//   // ============================================================

//   const hasActiveFilters = Boolean(search) || activeTab !== "all";

//   // ============================================================
//   // EMPTY STATE
//   // ============================================================

//   const hasOrganizations = organizations.length > 0;

//   const hasSearchOrFilterResult = hasActiveFilters && !hasOrganizations;

//   // ============================================================
//   // INITIAL PAGE LOADING
//   //
//   // Only the first page load uses a full-page spinner.
//   // Search/tab changes never enter this branch because
//   // initialLoading becomes false after the first request.
//   // ============================================================

//   if (initialLoading) {
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

//   // ============================================================
//   // INITIAL LOAD ERROR
//   // ============================================================

//   if (error && !hasOrganizations && !hasActiveFilters) {
//     return (
//       <Box sx={{ p: 3 }}>
//         <Alert severity="error">{error}</Alert>
//       </Box>
//     );
//   }

//   // ============================================================
//   // PAGE
//   // ============================================================

//   return (
//     <>
//       {/* ======================================================
//           BREADCRUMB
//       ====================================================== */}

//       <Breadcrumb items={breadcrumbItems} />

//       {/* ======================================================
//           HEADER
//       ====================================================== */}

//       <Header
//         title="Organizations"
//         description="Manage your client organizations and their social presence."
//         buttonLabel="New Organization"
//         buttonPath="/organizations/new"
//       />

//       {/* ======================================================
//           STATISTICS
//       ====================================================== */}

//       <StatsCards items={statistics} />

//       {/* ======================================================
//           SEARCH + FILTERS + GRID
//       ====================================================== */}

//       <Box
//         sx={{
//           position: "relative",
//         }}
//       >
//         {/* ==================================================
//             BACKGROUND REFRESH INDICATOR
//         ================================================== */}

//         {/* {refreshing && (
//           <Box
//             sx={{
//               position: "absolute",

//               top: 8,
//               right: 16,

//               zIndex: 10,

//               display: "flex",
//               alignItems: "center",
//               gap: 1,

//               px: 1.25,
//               py: 0.75,

//               borderRadius: "8px",

//               backgroundColor: "#FFFFFF",

//               border: "1px solid #E2E8F0",

//               boxShadow: "0 4px 14px rgba(15, 23, 42, 0.06)",
//             }}
//           >
//             <CircularProgress size={14} />

//             <Typography
//               sx={{
//                 fontSize: "12px",
//                 fontWeight: 500,
//                 lineHeight: "18px",
//                 color: "#64748B",
//               }}
//             >
//               Updating...
//             </Typography>
//           </Box>
//         )} */}

//         <SearchTabs
//           search={searchInput}
//           onSearchChange={handleSearchChange}
//           activeTab={activeTab}
//           onTabChange={handleTabChange}
//           counts={counts}
//         >
//           {/* ==================================================
//               NO FILTER / NO DATA
//           ================================================== */}

//           {!hasOrganizations && !hasSearchOrFilterResult && (
//             <Stack
//               alignItems="center"
//               justifyContent="center"
//               sx={{
//                 minHeight: 280,
//                 textAlign: "center",
//               }}
//             >
//               <Typography
//                 sx={{
//                   fontSize: "16px",
//                   fontWeight: 700,
//                   lineHeight: "24px",
//                   color: "#111827",
//                 }}
//               >
//                 No organizations found
//               </Typography>

//               <Typography
//                 sx={{
//                   mt: 0.5,
//                   fontSize: "13px",
//                   fontWeight: 400,
//                   lineHeight: "20px",
//                   color: "#64748B",
//                 }}
//               >
//                 Organizations will appear here once they are created.
//               </Typography>
//             </Stack>
//           )}

//           {/* ==================================================
//               SEARCH / FILTER NO MATCH
//           ================================================== */}

//           {!hasOrganizations && hasSearchOrFilterResult && (
//             <Stack
//               alignItems="center"
//               justifyContent="center"
//               sx={{
//                 minHeight: 280,
//                 textAlign: "center",
//               }}
//             >
//               <Typography
//                 sx={{
//                   fontSize: "16px",
//                   fontWeight: 700,
//                   lineHeight: "24px",
//                   color: "#111827",
//                 }}
//               >
//                 No matching organizations
//               </Typography>

//               <Typography
//                 sx={{
//                   mt: 0.5,
//                   fontSize: "13px",
//                   fontWeight: 400,
//                   lineHeight: "20px",
//                   color: "#64748B",
//                 }}
//               >
//                 Try changing your search or filter.
//               </Typography>
//             </Stack>
//           )}

//           {/* ==================================================
//               ORGANIZATION GRID
//           ================================================== */}

//           {hasOrganizations && (
//             <OrganizationGrid
//               organizations={organizations}
//               onOrganizationClick={handleOrganizationClick}
//               loading={refreshing}
//             />
//           )}
//         </SearchTabs>
//       </Box>

//       {/* ======================================================
//           BACKGROUND ERROR
//       ====================================================== */}

//       {error && (
//         <Alert
//           severity="error"
//           sx={{
//             mt: 2,
//             borderRadius: "12px",
//           }}
//         >
//           {error}
//         </Alert>
//       )}
//     </>
//   );
// }

import {
  Alert,
  Box,
  Pagination,
  Stack,
  Typography,
} from "@mui/material";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
import TrendingUpOutlinedIcon from "@mui/icons-material/TrendingUpOutlined";
import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import CampaignOutlinedIcon from "@mui/icons-material/CampaignOutlined";

import { useNavigate } from "react-router-dom";

import Header from "../../components/organization/list/Header";
import StatsCards from "../../components/organization/list/StatsCards";
import SearchTabs from "../../components/organization/list/SearchTabs";
import OrganizationGrid from "../../components/organization/list/OrganizationGrid";
import LoadingState from "../../components/ui/LoadingState";

import organizationService from "../../services/organization/organization.service";

export default function OrganizationList() {
  const navigate = useNavigate();

  // ============================================================
  // ORGANIZATION DATA
  // ============================================================

  const [organizations, setOrganizations] = useState([]);

  // ============================================================
  // SEARCH / FILTER STATE
  // ============================================================

  const [searchInput, setSearchInput] = useState("");

  const [search, setSearch] = useState("");

  const [activeTab, setActiveTab] = useState("all");

  // ============================================================
  // PAGINATION STATE
  // ============================================================

  const [page, setPage] = useState(1);

  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 10,
    total_items: 0,
    total_pages: 1,
    has_next: false,
    has_previous: false,
  });

  // ============================================================
  // LOADING STATE
  // ============================================================

  const [initialLoading, setInitialLoading] = useState(true);

  const [refreshing, setRefreshing] = useState(false);

  // ============================================================
  // ERROR STATE
  // ============================================================

  const [error, setError] = useState(null);

  // ============================================================
  // GLOBAL SUMMARY
  // ============================================================

  const [summary, setSummary] = useState({
    total_clients: 0,
    active_organizations: 0,
    inactive_organizations: 0,
    connected_accounts: 0,
    active_subscriptions: 0,
  });

  // ============================================================
  // INITIAL REQUEST TRACKING
  // ============================================================

  const isFirstLoad = useRef(true);
  const loadRequestId = useRef(0);

  // ============================================================
  // SEARCH DEBOUNCE
  // ============================================================

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(searchInput.trim());
    }, 400);

    return () => {
      window.clearTimeout(timer);
    };
  }, [searchInput]);

  // ============================================================
  // LOAD ORGANIZATIONS
  // ============================================================

  const loadOrganizations = useCallback(async () => {
    const requestId = loadRequestId.current + 1;
    loadRequestId.current = requestId;

    try {
      setError(null);

      if (isFirstLoad.current) {
        setInitialLoading(true);
      } else {
        setRefreshing(true);
      }

      const status =
        activeTab === "active"
          ? "ACTIVE"
          : activeTab === "inactive"
            ? "INACTIVE"
            : "";

      const response = await organizationService.getOrganizations({
        search,
        status,
        page,
        pageSize: 10,
        ordering: "-created_at",
      });

      if (requestId !== loadRequestId.current) {
        return;
      }

      if (!response?.success) {
        throw new Error(response?.message || "Unable to load organizations.");
      }

      const responseData = response?.data;

      const nextOrganizations = Array.isArray(responseData?.items)
        ? responseData.items
        : [];

      const nextSummary = responseData?.summary || {
        total_clients: 0,
        active_organizations: 0,
        inactive_organizations: 0,
        connected_accounts: 0,
        active_subscriptions: 0,
      };

      const nextPagination = responseData?.pagination || {
        page: 1,
        page_size: 10,
        total_items: 0,
        total_pages: 1,
        has_next: false,
        has_previous: false,
      };

      setOrganizations(nextOrganizations);

      setSummary(nextSummary);

      setPagination(nextPagination);
    } catch (error) {
      if (requestId !== loadRequestId.current) {
        return;
      }

      console.error("Failed to load organizations:", error);

      const errorMessage =
        error?.response?.data?.message ||
        error?.message ||
        "Unable to load organizations.";

      setError(errorMessage);

      /*
       * During background refresh we intentionally keep the
       * existing organizations and summary on screen.
       */

      if (isFirstLoad.current) {
        setOrganizations([]);

        setSummary({
          total_clients: 0,
          active_organizations: 0,
          inactive_organizations: 0,
          connected_accounts: 0,
          active_subscriptions: 0,
        });

        setPagination({
          page: 1,
          page_size: 10,
          total_items: 0,
          total_pages: 1,
          has_next: false,
          has_previous: false,
        });
      }
    } finally {
      if (requestId === loadRequestId.current) {
        setInitialLoading(false);
        setRefreshing(false);

        isFirstLoad.current = false;
      }
    }
  }, [activeTab, search, page]);

  // ============================================================
  // FETCH DATA
  // ============================================================

  useEffect(() => {
    loadOrganizations();
  }, [loadOrganizations]);

  // ============================================================
  // TAB COUNTS
  //
  // Always use global summary values.
  // Search/filter must not change the counts.
  // ============================================================

  const counts = useMemo(
    () => ({
      all: summary.total_clients || 0,

      active: summary.active_organizations || 0,

      inactive: summary.inactive_organizations || 0,
    }),
    [
      summary.total_clients,
      summary.active_organizations,
      summary.inactive_organizations,
    ],
  );

  // ============================================================
  // STATISTICS
  // ============================================================

  const statistics = useMemo(
    () => [
      {
        title: "Total Clients",
        value: summary.total_clients || 0,
        icon: BusinessOutlinedIcon,
      },
      {
        title: "Active Organizations",
        value: summary.active_organizations || 0,
        icon: TrendingUpOutlinedIcon,
      },
      {
        title: "Connected Accounts",
        value: summary.connected_accounts || 0,
        icon: GroupsOutlinedIcon,
      },
      {
        title: "Active Subscriptions",
        value: summary.active_subscriptions || 0,
        icon: CampaignOutlinedIcon,
      },
    ],
    [summary],
  );

  // ============================================================
  // TAB CHANGE
  // ============================================================

  const handleTabChange = useCallback((tab) => {
    setPage(1);
    setActiveTab(tab);
  }, []);

  // ============================================================
  // SEARCH CHANGE
  // ============================================================

  const handleSearchChange = useCallback((value) => {
    setPage(1);
    setSearchInput(value);
  }, []);

  // ============================================================
  // CLEAR SEARCH
  //
  // SearchTabs currently owns the search field.
  // Clearing search means setting it to empty.
  // ============================================================

  const handleClearSearch = useCallback(() => {
    setPage(1);
    setSearchInput("");
  }, []);

  // ============================================================
  // ORGANIZATION CLICK
  // ============================================================

  const handleOrganizationClick = useCallback(
    (organization) => {
      const organizationId = organization?.organization_id;

      if (!organizationId) {
        return;
      }

      navigate(`/organizations/${organizationId}/overview`);
    },
    [navigate],
  );

  // ============================================================
  // FILTER STATE
  // ============================================================

  const hasActiveFilters = Boolean(search) || activeTab !== "all";

  // ============================================================
  // EMPTY STATE
  // ============================================================

  const hasOrganizations = organizations.length > 0;

  const hasSearchOrFilterResult = hasActiveFilters && !hasOrganizations;

  // ============================================================
  // INITIAL PAGE LOADING
  //
  // Only the first page load uses a full-page spinner.
  // Search/tab changes never enter this branch because
  // initialLoading becomes false after the first request.
  // ============================================================

  if (initialLoading) {
    return <LoadingState page="Organizations" />;
  }

  // ============================================================
  // INITIAL LOAD ERROR
  // ============================================================

  if (error && !hasOrganizations && !hasActiveFilters) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ borderRadius: "16px", border: "1px solid rgba(255,255,255,.85)", boxShadow: "0 6px 16px rgba(77, 59, 75, .08)" }}>{error}</Alert>
      </Box>
    );
  }

  // ============================================================
  // PAGE
  // ============================================================

  return (
    <>
      {/* ======================================================
          HEADER
      ====================================================== */}

      <Header
        title="Organizations"
        description="Manage your client organizations and their social presence."
        buttonLabel="New Organization"
        buttonPath="/organizations/new"
      />

      {/* ======================================================
          STATISTICS
      ====================================================== */}

      <StatsCards items={statistics} />

      {/* ======================================================
          SEARCH + FILTERS + GRID
      ====================================================== */}

      <Box
        sx={{
          position: "relative",
        }}
      >
        {/* ==================================================
            BACKGROUND REFRESH INDICATOR
        ================================================== */}

        {/* {refreshing && (
          <Box
            sx={{
              position: "absolute",

              top: 8,
              right: 16,

              zIndex: 10,

              display: "flex",
              alignItems: "center",
              gap: 1,

              px: 1.25,
              py: 0.75,

              borderRadius: "8px",

              backgroundColor: "#FFFFFF",

              border: "1px solid #E2E8F0",

              boxShadow: "0 4px 14px rgba(15, 23, 42, 0.06)",
            }}
          >
            <CircularProgress size={14} />

            <Typography
              sx={{
                fontSize: "12px",
                fontWeight: 500,
                lineHeight: "18px",
                color: "#64748B",
              }}
            >
              Updating...
            </Typography>
          </Box>
        )} */}

        <SearchTabs
          search={searchInput}
          onSearchChange={handleSearchChange}
          activeTab={activeTab}
          onTabChange={handleTabChange}
          counts={counts}
        >
          <Box sx={{ position: "relative" }}>
          {/* ==================================================
              NO FILTER / NO DATA
          ================================================== */}

          {!hasOrganizations && !hasSearchOrFilterResult && (
            <Stack
              alignItems="center"
              justifyContent="center"
              sx={{
                minHeight: 280,
                textAlign: "center",
                px: 2,
              }}
            >
              <Box sx={{ width: 58, height: 58, mb: 2, display: "grid", placeItems: "center", borderRadius: "50%", color: "#705AD1", background: "linear-gradient(145deg, #F0ECFF, #FFFFFF)", border: "1px solid rgba(255,255,255,.95)", boxShadow: "0 6px 15px rgba(91, 87, 165, .13), inset 0 1px 0 #fff" }}>
                <BusinessOutlinedIcon sx={{ fontSize: 27 }} />
              </Box>
              <Typography
                sx={{
                  fontSize: "16px",
                  fontWeight: 700,
                  lineHeight: "24px",
                  color: "#17294D",
                }}
              >
                No organizations found
              </Typography>

              <Typography
                sx={{
                  mt: 0.5,
                  fontSize: "13px",
                  fontWeight: 400,
                  lineHeight: "20px",
                  color: "#64748B",
                }}
              >
                Organizations will appear here once they are created.
              </Typography>
            </Stack>
          )}

          {/* ==================================================
              SEARCH / FILTER NO MATCH
          ================================================== */}

          {!hasOrganizations && hasSearchOrFilterResult && (
            <Stack
              alignItems="center"
              justifyContent="center"
              sx={{
                minHeight: 280,
                textAlign: "center",
                px: 2,
              }}
            >
              <Box sx={{ width: 58, height: 58, mb: 2, display: "grid", placeItems: "center", borderRadius: "50%", color: "#5685CC", background: "linear-gradient(145deg, #EAF4FF, #FFFFFF)", border: "1px solid rgba(255,255,255,.95)", boxShadow: "0 6px 15px rgba(72, 117, 170, .12), inset 0 1px 0 #fff" }}>
                <BusinessOutlinedIcon sx={{ fontSize: 27 }} />
              </Box>
              <Typography
                sx={{
                  fontSize: "16px",
                  fontWeight: 700,
                  lineHeight: "24px",
                  color: "#17294D",
                }}
              >
                No matching organizations
              </Typography>

              <Typography
                sx={{
                  mt: 0.5,
                  fontSize: "13px",
                  fontWeight: 400,
                  lineHeight: "20px",
                  color: "#64748B",
                }}
              >
                Try changing your search or filter.
              </Typography>
            </Stack>
          )}

          {/* ==================================================
              ORGANIZATION GRID
          ================================================== */}

          {hasOrganizations && (
            <OrganizationGrid
              organizations={organizations}
              onOrganizationClick={handleOrganizationClick}
            />
          )}
          {refreshing && (
            <LoadingState page="Organizations" variant="overlay" />
          )}
          </Box>
        </SearchTabs>
      </Box>

      {/* ======================================================
          PAGINATION
      ====================================================== */}

      {pagination.total_pages > 1 && (
        <Box
          sx={{
            mt: 3,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <Pagination
            count={pagination.total_pages}
            page={pagination.page}
            onChange={(_, value) => setPage(value)}
            color="primary"
            shape="rounded"
            showFirstButton
            showLastButton
            sx={{
              "& .MuiPaginationItem-root": {
                color: "#536A8A",
                borderRadius: "11px",
                border: "1px solid rgba(255,255,255,.85)",
                background: "linear-gradient(145deg, rgba(255,255,255,.82), rgba(235,243,255,.75))",
                boxShadow: "0 2px 7px rgba(74, 100, 145, .07), inset 0 1px 0 #fff",
              },
              "& .MuiPaginationItem-root.Mui-selected": {
                color: "#355FBC",
                background: "linear-gradient(145deg, #E4EDFF, #F6F8FF)",
                borderColor: "rgba(123, 153, 211, .42)",
              },
            }}
          />
        </Box>
      )}

      {/* ======================================================
          BACKGROUND ERROR
      ====================================================== */}

      {error && (
        <Alert
          severity="error"
          sx={{
            mt: 2,
            borderRadius: "16px",
            border: "1px solid rgba(255,255,255,.85)",
            boxShadow: "0 6px 16px rgba(77, 59, 75, .08)",
          }}
        >
          {error}
        </Alert>
      )}
    </>
  );
}
