// import { Alert, Box, CircularProgress, Snackbar } from "@mui/material";

// import { useCallback, useEffect, useState } from "react";

// import { useNavigate, useParams } from "react-router-dom";

// import metaService from "../../services/social/meta.service";

// // ============================================================
// // OVERVIEW COMPONENTS
// // ============================================================

// import OverviewHeader from "../../components/organization/overview/OverviewHeader";

// import OverviewLayout from "../../components/organization/overview/OverviewLayout";

// import OrganizationProfileCard from "../../components/organization/overview/cards/OrganizationProfileCard";

// import BrandInformationCard from "../../components/organization/overview/cards/BrandInformationCard";

// import ContactInformationCard from "../../components/organization/overview/cards/ContactInformationCard";

// import SubscriptionCard from "../../components/organization/overview/cards/SubscriptionCard";

// import ActivityTimelineCard from "../../components/organization/overview/cards/ActivityTimelineCard";

// // ============================================================
// // SOCIAL ACCOUNTS
// // ============================================================

// import SocialAccountsSection from "../../components/organization/social/SocialAccountsSection";

// // ============================================================
// // UI DIALOGS
// // ============================================================

// import ConfirmDialog from "../../components/ui/dialog/ConfirmDialog";

// // ============================================================
// // SUBSCRIPTION DIALOGS
// // ============================================================

// import RenewSubscriptionDialog from "../../components/organization/subscription/RenewSubscriptionDialog";

// import ChangePlanDialog from "../../components/organization/subscription/ChangePlanDialog";

// import StartSubscriptionDialog from "../../components/organization/subscription/StartSubscriptionDialog";

// import CancelSubscriptionDialog from "../../components/organization/subscription/CancelSubscriptionDialog";

// import SubscriptionHistoryDrawer from "../../components/organization/subscription/SubscriptionHistoryDrawer";

// // ============================================================
// // HOOKS
// // ============================================================

// import useOrganizationSubscription from "../../hooks/organization/useOrganizationSubscription";

// // ============================================================
// // SERVICES
// // ============================================================

// import organizationService from "../../services/organization/organization.service";

// import plansService from "../../services/plans.service";

// // ============================================================
// // ORGANIZATION OVERVIEW
// // ============================================================

// export default function OrganizationOverview() {
//   const navigate = useNavigate();

//   const { organizationId } = useParams();

//   // ============================================================
//   // ORGANIZATION STATE
//   // ============================================================

//   const [organization, setOrganization] = useState(null);

//   const [loading, setLoading] = useState(true);

//   const [error, setError] = useState(null);

//   // ============================================================
//   // DELETE STATE
//   // ============================================================

//   const [deleteOpen, setDeleteOpen] = useState(false);

//   const [deleting, setDeleting] = useState(false);

//   // ============================================================
//   // ACTIVE PLANS STATE
//   // ============================================================

//   const [activePlans, setActivePlans] = useState([]);

//   const [plansLoading, setPlansLoading] = useState(false);

//   const [plansError, setPlansError] = useState(null);

//   // ============================================================
//   // SUBSCRIPTION DIALOG STATE
//   // ============================================================

//   const [renewOpen, setRenewOpen] = useState(false);

//   const [changePlanOpen, setChangePlanOpen] = useState(false);

//   const [startSubscriptionOpen, setStartSubscriptionOpen] = useState(false);

//   const [cancelSubscriptionOpen, setCancelSubscriptionOpen] = useState(false);

//   const [subscriptionHistoryOpen, setSubscriptionHistoryOpen] = useState(false);

//   // ============================================================
//   // SOCIAL CONNECT STATE
//   // ============================================================

//   const [connectingPlatform, setConnectingPlatform] = useState(null);

//   const [socialConnectError, setSocialConnectError] = useState("");

//   const [socialConnectSuccess, setSocialConnectSuccess] = useState("");

//   // ============================================================
//   // SOCIAL ACCOUNTS REFRESH
//   // ============================================================
//   //
//   // Backend completes Meta connection before redirecting here.
//   //
//   // Incrementing this value tells SocialAccountsSection to
//   // refresh its useSocialAccounts hook.
//   //
//   // ============================================================

//   const [socialAccountsRefreshKey, setSocialAccountsRefreshKey] = useState(0);

//   // ============================================================
//   // HELPERS
//   // ============================================================

//   const showSuccess = useCallback((message) => {
//     setSocialConnectSuccess(message);
//   }, []);

//   const showError = useCallback((message) => {
//     setSocialConnectError(message);
//   }, []);

//   const refreshSocialAccounts = useCallback(() => {
//     setSocialAccountsRefreshKey((current) => current + 1);
//   }, []);

//   // ============================================================
//   // LOAD ORGANIZATION
//   // ============================================================

//   const loadOrganization = useCallback(async () => {
//     if (!organizationId) {
//       setError("Organization ID is missing.");
//       setLoading(false);

//       return;
//     }

//     try {
//       setLoading(true);
//       setError(null);

//       const response =
//         await organizationService.getOrganization(organizationId);

//       if (!response?.success) {
//         throw new Error(response?.message || "Unable to load organization.");
//       }

//       if (!response?.data) {
//         throw new Error("Organization data was not returned.");
//       }

//       setOrganization(response.data);
//     } catch (error) {
//       console.error("Failed to load organization:", error);

//       setError(
//         error?.response?.data?.message ||
//           error?.message ||
//           "Unable to load organization.",
//       );
//     } finally {
//       setLoading(false);
//     }
//   }, [organizationId]);

//   // ============================================================
//   // LOAD ORGANIZATION ON MOUNT / ID CHANGE
//   // ============================================================

//   useEffect(() => {
//     loadOrganization();
//   }, [loadOrganization]);

//   // ============================================================
//   // HANDLE SOCIAL OAUTH CALLBACK
//   // ============================================================
//   //
//   // Backend redirects:
//   //
//   // SUCCESS:
//   //
//   // ?social_connect=success
//   // &platform=meta
//   // &accounts_connected=2
//   //
//   // ERROR:
//   //
//   // ?social_connect=error
//   // &platform=meta
//   // &reason=...
//   //
//   // No frontend account selection happens here.
//   //
//   // ============================================================

//   useEffect(() => {
//     const params = new URLSearchParams(window.location.search);

//     const socialConnect = params.get("social_connect");

//     const platform = params.get("platform");

//     const accountsConnected = params.get("accounts_connected");

//     const reason = params.get("reason");

//     if (!socialConnect) {
//       return;
//     }

//     if (socialConnect === "success") {
//       setConnectingPlatform(null);

//       if (platform === "meta") {
//         const count = Number(accountsConnected || 0);

//         showSuccess(
//           count > 0
//             ? `${count} Meta account(s) connected successfully.`
//             : "Meta accounts connected successfully.",
//         );
//       } else {
//         showSuccess("Social account connected successfully.");
//       }

//       // Backend has already saved the accounts.
//       // Refresh the connected accounts list.
//       refreshSocialAccounts();
//     }

//     if (socialConnect === "error") {
//       setConnectingPlatform(null);

//       showError(reason || "Unable to connect Meta accounts.");
//     }

//     // ==========================================================
//     // CLEAN OAUTH QUERY PARAMETERS
//     // ==========================================================

//     params.delete("social_connect");
//     params.delete("platform");
//     params.delete("accounts_connected");
//     params.delete("organization_id");
//     params.delete("reason");

//     const queryString = params.toString();

//     const cleanUrl =
//       `${window.location.pathname}` + `${queryString ? `?${queryString}` : ""}`;

//     window.history.replaceState({}, document.title, cleanUrl);
//   }, [refreshSocialAccounts, showError, showSuccess]);

//   // ============================================================
//   // LOAD ACTIVE PLANS
//   // ============================================================

//   const loadActivePlans = useCallback(async () => {
//     try {
//       setPlansLoading(true);
//       setPlansError(null);

//       const plans = await plansService.getPlans({
//         status: "active",
//       });

//       if (!Array.isArray(plans)) {
//         throw new Error("Invalid plans response.");
//       }

//       setActivePlans(plans);

//       return plans;
//     } catch (error) {
//       console.error("Failed to load active plans:", error);

//       setPlansError(
//         error?.response?.data?.message ||
//           error?.message ||
//           "Unable to load active subscription plans.",
//       );

//       setActivePlans([]);

//       return [];
//     } finally {
//       setPlansLoading(false);
//     }
//   }, []);

//   // ============================================================
//   // REFRESH ORGANIZATION
//   // ============================================================

//   const refreshOrganization = useCallback(async () => {
//     await loadOrganization();
//   }, [loadOrganization]);

//   // ============================================================
//   // SUBSCRIPTION HOOK
//   // ============================================================

//   const {
//     loading: subscriptionActionLoading,

//     error: subscriptionActionError,

//     renew,

//     changePlan,

//     start,

//     cancel,

//     clearError: clearSubscriptionError,

//     history,

//     historyLoading,

//     historyError,

//     loadHistory,

//     clearHistoryError,
//   } = useOrganizationSubscription({
//     organizationId,

//     onSuccess: refreshOrganization,
//   });

//   // ============================================================
//   // OPEN SUBSCRIPTION HISTORY
//   // ============================================================

//   const handleOpenHistory = async () => {
//     clearSubscriptionError();

//     clearHistoryError();

//     setSubscriptionHistoryOpen(true);

//     await loadHistory();
//   };

//   // ============================================================
//   // OPEN RENEW
//   // ============================================================

//   const handleOpenRenew = () => {
//     clearSubscriptionError();

//     setRenewOpen(true);
//   };

//   // ============================================================
//   // OPEN CHANGE PLAN
//   // ============================================================

//   const handleOpenChangePlan = async () => {
//     clearSubscriptionError();

//     if (activePlans.length === 0) {
//       await loadActivePlans();
//     }

//     setChangePlanOpen(true);
//   };

//   // ============================================================
//   // OPEN START SUBSCRIPTION
//   // ============================================================

//   const handleOpenStartSubscription = async () => {
//     clearSubscriptionError();

//     if (activePlans.length === 0) {
//       await loadActivePlans();
//     }

//     setStartSubscriptionOpen(true);
//   };

//   // ============================================================
//   // OPEN CANCEL
//   // ============================================================

//   const handleOpenCancel = () => {
//     clearSubscriptionError();

//     setCancelSubscriptionOpen(true);
//   };

//   // ============================================================
//   // RENEW SUBSCRIPTION
//   // ============================================================

//   const handleRenew = async ({ billingCycle }) => {
//     const response = await renew({
//       billingCycle,
//     });

//     if (response) {
//       setRenewOpen(false);
//     }
//   };

//   // ============================================================
//   // CHANGE PLAN
//   // ============================================================

//   const handleChangePlan = async ({ plan, billingCycle }) => {
//     const response = await changePlan({
//       plan,
//       billingCycle,
//     });

//     if (response) {
//       setChangePlanOpen(false);
//     }
//   };

//   // ============================================================
//   // START SUBSCRIPTION
//   // ============================================================

//   const handleStartSubscription = async ({ plan, billingCycle }) => {
//     const response = await start({
//       plan,
//       billingCycle,
//     });

//     if (response) {
//       setStartSubscriptionOpen(false);
//     }
//   };

//   // ============================================================
//   // CANCEL SUBSCRIPTION
//   // ============================================================

//   const handleCancelSubscription = async () => {
//     const response = await cancel();

//     if (response) {
//       setCancelSubscriptionOpen(false);
//     }
//   };

//   // ============================================================
//   // DELETE ORGANIZATION
//   // ============================================================

//   const handleDelete = async () => {
//     if (!organizationId || deleting) {
//       return;
//     }

//     try {
//       setDeleting(true);
//       setError(null);

//       const response =
//         await organizationService.deleteOrganization(organizationId);

//       if (!response?.success) {
//         throw new Error(response?.message || "Unable to delete organization.");
//       }

//       setDeleteOpen(false);

//       navigate("/organizations");
//     } catch (error) {
//       console.error("Failed to delete organization:", error);

//       setError(
//         error?.response?.data?.message ||
//           error?.message ||
//           "Unable to delete organization. Please try again.",
//       );
//     } finally {
//       setDeleting(false);
//     }
//   };

//   // ============================================================
//   // CONNECT SOCIAL ACCOUNT
//   // ============================================================
//   //
//   // META:
//   // - Facebook Page
//   // - linked Instagram Professional account
//   //
//   // No frontend Page selection.
//   //
//   // LINKEDIN / YOUTUBE:
//   // - Coming soon
//   //
//   // ============================================================

//   const handleSocialConnect = async (platform, selectedOrganizationId) => {
//     if (!selectedOrganizationId || selectedOrganizationId !== organizationId) {
//       setSocialConnectError("Organization is required.");

//       return;
//     }

//     // ==========================================================
//     // META
//     // ==========================================================

//     if (platform === "meta") {
//       try {
//         setSocialConnectError("");
//         setSocialConnectSuccess("");

//         setConnectingPlatform("meta");

//         await metaService.startOAuth(selectedOrganizationId);

//         // startOAuth normally redirects the browser.
//         // Keep this here only as a defensive fallback.
//       } catch (error) {
//         console.error("Failed to start Meta OAuth:", error);

//         setConnectingPlatform(null);

//         setSocialConnectError(
//           error?.response?.data?.message ||
//             error?.message ||
//             "Unable to start Meta connection. Please try again.",
//         );
//       }

//       return;
//     }

//     // ==========================================================
//     // LINKEDIN
//     // ==========================================================

//     if (platform === "linkedin") {
//       setSocialConnectError("LinkedIn integration is coming soon.");

//       return;
//     }

//     // ==========================================================
//     // YOUTUBE
//     // ==========================================================

//     if (platform === "youtube") {
//       setSocialConnectError("YouTube integration is coming soon.");

//       return;
//     }

//     // ==========================================================
//     // UNKNOWN PLATFORM
//     // ==========================================================

//     setSocialConnectError("This social platform is not available yet.");
//   };

//   // ============================================================
//   // INITIAL LOADING
//   // ============================================================

//   if (loading) {
//     return (
//       <Box
//         sx={{
//           minHeight: 500,
//           display: "flex",
//           alignItems: "center",
//           justifyContent: "center",
//         }}
//       >
//         <CircularProgress size={30} />
//       </Box>
//     );
//   }

//   // ============================================================
//   // ORGANIZATION LOAD ERROR
//   // ============================================================

//   if (error || !organization) {
//     return (
//       <Box
//         sx={{
//           maxWidth: 980,
//           mx: "auto",
//           p: 3,
//         }}
//       >
//         <Alert severity="error">{error || "Organization not found."}</Alert>
//       </Box>
//     );
//   }

//   // ============================================================
//   // SUBSCRIPTION STATE
//   // ============================================================

//   const hasCurrentSubscription = Boolean(organization.subscription_status);

//   const isSubscriptionActive = organization.subscription_status === "active";

//   // ============================================================
//   // RENDER
//   // ============================================================

//   return (
//     <>
//       {/* ======================================================
//           HEADER
//       ====================================================== */}

//       <OverviewHeader
//         organization={organization}
//         onEdit={() => navigate(`/organizations/${organizationId}/edit`)}
//         onDelete={() => setDeleteOpen(true)}
//       />

//       {/* ======================================================
//           PAGE LEVEL SUBSCRIPTION ERROR
//       ====================================================== */}

//       {(subscriptionActionError || plansError) && (
//         <Alert
//           severity="error"
//           sx={{
//             mb: 3,
//             borderRadius: "12px",
//           }}
//         >
//           {subscriptionActionError || plansError}
//         </Alert>
//       )}

//       {/* ======================================================
//           SOCIAL CONNECT ERROR
//       ====================================================== */}

//       {socialConnectError && (
//         <Alert
//           severity="error"
//           sx={{
//             mb: 3,
//             borderRadius: "12px",
//           }}
//           onClose={() => setSocialConnectError("")}
//         >
//           {socialConnectError}
//         </Alert>
//       )}

//       {/* ======================================================
//           OVERVIEW LAYOUT
//       ====================================================== */}

//       <OverviewLayout
//         brandInformation={<BrandInformationCard organization={organization} />}
//         contactInformation={
//           <ContactInformationCard organization={organization} />
//         }
//         socialAccounts={
//           <SocialAccountsSection
//             organizationId={organizationId}
//             onConnect={handleSocialConnect}
//             connectingPlatform={connectingPlatform}
//             refreshKey={socialAccountsRefreshKey}
//           />
//         }
//         activityTimeline={<ActivityTimelineCard organization={organization} />}
//         profile={<OrganizationProfileCard organization={organization} />}
//         subscription={
//           <SubscriptionCard
//             organization={organization}
//             onRenew={handleOpenRenew}
//             onChangePlan={
//               isSubscriptionActive ? handleOpenChangePlan : undefined
//             }
//             onCancel={isSubscriptionActive ? handleOpenCancel : undefined}
//             onStartSubscription={
//               !hasCurrentSubscription ? handleOpenStartSubscription : undefined
//             }
//             onViewHistory={handleOpenHistory}
//             actionLoading={subscriptionActionLoading}
//           />
//         }
//       />

//       {/* ======================================================
//           DELETE ORGANIZATION
//       ====================================================== */}

//       <ConfirmDialog
//         open={deleteOpen}
//         title="Delete organization"
//         message="Are you sure you want to delete"
//         entityName={organization.name}
//         description="This will also remove its social accounts, posts, and campaigns. This action cannot be undone."
//         confirmText="Delete"
//         cancelText="Cancel"
//         loading={deleting}
//         onClose={() => {
//           if (!deleting) {
//             setDeleteOpen(false);
//           }
//         }}
//         onConfirm={handleDelete}
//       />

//       {/* ======================================================
//           RENEW SUBSCRIPTION
//       ====================================================== */}

//       <RenewSubscriptionDialog
//         open={renewOpen}
//         organization={organization}
//         loading={subscriptionActionLoading}
//         error={subscriptionActionError}
//         onClose={() => {
//           if (!subscriptionActionLoading) {
//             setRenewOpen(false);

//             clearSubscriptionError();
//           }
//         }}
//         onSubmit={handleRenew}
//       />

//       {/* ======================================================
//           CHANGE PLAN
//       ====================================================== */}

//       <ChangePlanDialog
//         open={changePlanOpen}
//         organization={organization}
//         plans={activePlans}
//         loading={subscriptionActionLoading || plansLoading}
//         error={subscriptionActionError || plansError}
//         onClose={() => {
//           if (!subscriptionActionLoading) {
//             setChangePlanOpen(false);

//             clearSubscriptionError();
//           }
//         }}
//         onSubmit={handleChangePlan}
//       />

//       {/* ======================================================
//           START SUBSCRIPTION
//       ====================================================== */}

//       <StartSubscriptionDialog
//         open={startSubscriptionOpen}
//         plans={activePlans}
//         loading={subscriptionActionLoading || plansLoading}
//         error={subscriptionActionError || plansError}
//         onClose={() => {
//           if (!subscriptionActionLoading) {
//             setStartSubscriptionOpen(false);

//             clearSubscriptionError();
//           }
//         }}
//         onSubmit={handleStartSubscription}
//       />

//       {/* ======================================================
//           CANCEL SUBSCRIPTION
//       ====================================================== */}

//       <CancelSubscriptionDialog
//         open={cancelSubscriptionOpen}
//         organization={organization}
//         loading={subscriptionActionLoading}
//         error={subscriptionActionError}
//         onClose={() => {
//           if (!subscriptionActionLoading) {
//             setCancelSubscriptionOpen(false);

//             clearSubscriptionError();
//           }
//         }}
//         onConfirm={handleCancelSubscription}
//       />

//       {/* ======================================================
//           SUBSCRIPTION HISTORY
//       ====================================================== */}

//       <SubscriptionHistoryDrawer
//         open={subscriptionHistoryOpen}
//         onClose={() => {
//           if (!historyLoading) {
//             setSubscriptionHistoryOpen(false);

//             clearHistoryError();
//           }
//         }}
//         subscriptions={history}
//         loading={historyLoading}
//         error={historyError}
//       />

//       {/* ======================================================
//           SOCIAL CONNECT SUCCESS
//       ====================================================== */}

//       <Snackbar
//         open={Boolean(socialConnectSuccess)}
//         autoHideDuration={5000}
//         onClose={() => setSocialConnectSuccess("")}
//         anchorOrigin={{
//           vertical: "top",
//           horizontal: "right",
//         }}
//       >
//         <Alert
//           severity="success"
//           variant="filled"
//           onClose={() => setSocialConnectSuccess("")}
//         >
//           {socialConnectSuccess}
//         </Alert>
//       </Snackbar>
//     </>
//   );
// }

import { Alert, Box, CircularProgress, Snackbar } from "@mui/material";

import { useCallback, useEffect, useState } from "react";

import { useNavigate, useParams } from "react-router-dom";

import metaService from "../../services/social/meta.service";

// ============================================================
// OVERVIEW COMPONENTS
// ============================================================

import OverviewHeader from "../../components/organization/overview/OverviewHeader";

import OverviewLayout from "../../components/organization/overview/OverviewLayout";

import OrganizationProfileCard from "../../components/organization/overview/cards/OrganizationProfileCard";

import BrandInformationCard from "../../components/organization/overview/cards/BrandInformationCard";

import ContactInformationCard from "../../components/organization/overview/cards/ContactInformationCard";

import SubscriptionCard from "../../components/organization/overview/cards/SubscriptionCard";

import ActivityTimelineCard from "../../components/organization/overview/cards/ActivityTimelineCard";

// ============================================================
// SOCIAL ACCOUNTS
// ============================================================

import SocialAccountsSection from "../../components/organization/social/SocialAccountsSection";

import MetaPageSelectionDialog from "../../components/organization/social/MetaPageSelectionDialog";

// ============================================================
// UI DIALOGS
// ============================================================

import ConfirmDialog from "../../components/ui/dialog/ConfirmDialog";

// ============================================================
// SUBSCRIPTION DIALOGS
// ============================================================

import RenewSubscriptionDialog from "../../components/organization/subscription/RenewSubscriptionDialog";

import ChangePlanDialog from "../../components/organization/subscription/ChangePlanDialog";

import StartSubscriptionDialog from "../../components/organization/subscription/StartSubscriptionDialog";

import CancelSubscriptionDialog from "../../components/organization/subscription/CancelSubscriptionDialog";

import SubscriptionHistoryDrawer from "../../components/organization/subscription/SubscriptionHistoryDrawer";

// ============================================================
// HOOKS
// ============================================================

import useOrganizationSubscription from "../../hooks/organization/useOrganizationSubscription";

// ============================================================
// SERVICES
// ============================================================

import organizationService from "../../services/organization/organization.service";

import plansService from "../../services/plans.service";

// ============================================================
// ORGANIZATION OVERVIEW
// ============================================================

export default function OrganizationOverview() {
  const navigate = useNavigate();

  const { organizationId } = useParams();

  // ============================================================
  // ORGANIZATION STATE
  // ============================================================

  const [organization, setOrganization] = useState(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState(null);

  // ============================================================
  // DELETE STATE
  // ============================================================

  const [deleteOpen, setDeleteOpen] = useState(false);

  const [deleting, setDeleting] = useState(false);

  // ============================================================
  // ACTIVE PLANS STATE
  // ============================================================

  const [activePlans, setActivePlans] = useState([]);

  const [plansLoading, setPlansLoading] = useState(false);

  const [plansError, setPlansError] = useState(null);

  // ============================================================
  // SUBSCRIPTION DIALOG STATE
  // ============================================================

  const [renewOpen, setRenewOpen] = useState(false);

  const [changePlanOpen, setChangePlanOpen] = useState(false);

  const [startSubscriptionOpen, setStartSubscriptionOpen] = useState(false);

  const [cancelSubscriptionOpen, setCancelSubscriptionOpen] = useState(false);

  const [subscriptionHistoryOpen, setSubscriptionHistoryOpen] = useState(false);

  // ============================================================
  // SOCIAL CONNECT STATE
  // ============================================================

  const [connectingPlatform, setConnectingPlatform] = useState(null);

  const [socialConnectError, setSocialConnectError] = useState("");

  const [socialConnectSuccess, setSocialConnectSuccess] = useState("");

  // ============================================================
  // META PAGE SELECTION STATE
  // ============================================================

  const [metaSelectionOpen, setMetaSelectionOpen] = useState(false);

  const [metaSelectionLoading, setMetaSelectionLoading] = useState(false);

  const [metaSelectionSubmitting, setMetaSelectionSubmitting] = useState(false);

  const [metaSelectionError, setMetaSelectionError] = useState("");

  const [metaSelectionPages, setMetaSelectionPages] = useState([]);

  const [metaSelectionKey, setMetaSelectionKey] = useState("");

  // ============================================================
  // SOCIAL ACCOUNTS REFRESH
  // ============================================================

  const [socialAccountsRefreshKey, setSocialAccountsRefreshKey] = useState(0);

  // ============================================================
  // HELPERS
  // ============================================================

  const showSuccess = useCallback((message) => {
    setSocialConnectSuccess(message);
  }, []);

  const showError = useCallback((message) => {
    setSocialConnectError(message);
  }, []);

  const refreshSocialAccounts = useCallback(() => {
    setSocialAccountsRefreshKey((current) => current + 1);
  }, []);

  // ============================================================
  // LOAD ORGANIZATION
  // ============================================================

  const loadOrganization = useCallback(async () => {
    if (!organizationId) {
      setError("Organization ID is missing.");
      setLoading(false);

      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response =
        await organizationService.getOrganization(organizationId);

      if (!response?.success) {
        throw new Error(response?.message || "Unable to load organization.");
      }

      if (!response?.data) {
        throw new Error("Organization data was not returned.");
      }

      setOrganization(response.data);
    } catch (error) {
      console.error("Failed to load organization:", error);

      setError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to load organization.",
      );
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  // ============================================================
  // LOAD ORGANIZATION
  // ============================================================

  useEffect(() => {
    loadOrganization();
  }, [loadOrganization]);

  // ============================================================
  // LOAD META PAGE SELECTION
  // ============================================================

  const loadMetaSelection = useCallback(
    async (selectionKey) => {
      if (!organizationId || !selectionKey) {
        return;
      }

      try {
        setMetaSelectionLoading(true);
        setMetaSelectionError("");

        setMetaSelectionKey(selectionKey);

        const response = await metaService.getOAuthSelection(
          organizationId,
          selectionKey,
        );

        const pages = response?.data?.pages || [];

        setMetaSelectionPages(pages);

        setMetaSelectionOpen(true);
      } catch (error) {
        console.error("Failed to load Meta Page selection:", error);

        setMetaSelectionError(
          error?.response?.data?.message ||
            error?.message ||
            "Unable to load Meta Pages.",
        );

        setMetaSelectionPages([]);

        setMetaSelectionOpen(true);
      } finally {
        setMetaSelectionLoading(false);
      }
    },
    [organizationId],
  );

  // ============================================================
  // HANDLE META PAGE SELECTION CONFIRM
  // ============================================================

  const handleMetaPageSelection = useCallback(
    async (pageId) => {
      if (
        !organizationId ||
        !metaSelectionKey ||
        !pageId ||
        metaSelectionSubmitting
      ) {
        return;
      }

      try {
        setMetaSelectionSubmitting(true);
        setMetaSelectionError("");

        const response = await metaService.confirmOAuthSelection(
          organizationId,
          metaSelectionKey,
          pageId,
        );

        const data = response?.data || {};

        const count = Number(data.accounts_connected || 0);

        setMetaSelectionOpen(false);

        setMetaSelectionPages([]);

        setMetaSelectionKey("");

        setConnectingPlatform(null);

        showSuccess(
          count > 0
            ? `${count} Meta account(s) connected successfully.`
            : "Meta accounts connected successfully.",
        );

        refreshSocialAccounts();
      } catch (error) {
        console.error("Failed to confirm Meta Page selection:", error);

        setMetaSelectionError(
          error?.response?.data?.message ||
            error?.message ||
            "Unable to connect the selected Meta Page.",
        );
      } finally {
        setMetaSelectionSubmitting(false);
      }
    },
    [
      organizationId,
      metaSelectionKey,
      metaSelectionSubmitting,
      refreshSocialAccounts,
      showSuccess,
    ],
  );

  // ============================================================
  // HANDLE SOCIAL OAUTH CALLBACK
  // ============================================================

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);

    const socialConnect = params.get("social_connect");

    const platform = params.get("platform");

    const accountsConnected = params.get("accounts_connected");

    const reason = params.get("reason");

    const selectionKey = params.get("selection_key");

    if (!socialConnect) {
      return;
    }

    // ==========================================================
    // SELECTION REQUIRED
    // ==========================================================

    if (socialConnect === "selection" && platform === "meta") {
      setConnectingPlatform("meta");

      loadMetaSelection(selectionKey);
    }

    // ==========================================================
    // SUCCESS
    // ==========================================================

    if (socialConnect === "success") {
      setConnectingPlatform(null);

      if (platform === "meta") {
        const count = Number(accountsConnected || 0);

        showSuccess(
          count > 0
            ? `${count} Meta account(s) connected successfully.`
            : "Meta accounts connected successfully.",
        );
      } else {
        showSuccess("Social account connected successfully.");
      }

      refreshSocialAccounts();
    }

    // ==========================================================
    // ERROR
    // ==========================================================

    if (socialConnect === "error") {
      setConnectingPlatform(null);

      showError(reason || "Unable to connect Meta accounts.");
    }

    // ==========================================================
    // CLEAN OAUTH QUERY PARAMETERS
    // ==========================================================

    params.delete("social_connect");
    params.delete("platform");
    params.delete("accounts_connected");
    params.delete("organization_id");
    params.delete("reason");
    params.delete("selection_key");

    const queryString = params.toString();

    const cleanUrl =
      `${window.location.pathname}` + `${queryString ? `?${queryString}` : ""}`;

    window.history.replaceState({}, document.title, cleanUrl);
  }, [loadMetaSelection, refreshSocialAccounts, showError, showSuccess]);

  // ============================================================
  // LOAD ACTIVE PLANS
  // ============================================================

  const loadActivePlans = useCallback(async () => {
    try {
      setPlansLoading(true);
      setPlansError(null);

      const plans = await plansService.getPlans({
        status: "active",
      });

      if (!Array.isArray(plans)) {
        throw new Error("Invalid plans response.");
      }

      setActivePlans(plans);

      return plans;
    } catch (error) {
      console.error("Failed to load active plans:", error);

      setPlansError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to load active subscription plans.",
      );

      setActivePlans([]);

      return [];
    } finally {
      setPlansLoading(false);
    }
  }, []);

  // ============================================================
  // REFRESH ORGANIZATION
  // ============================================================

  const refreshOrganization = useCallback(async () => {
    await loadOrganization();
  }, [loadOrganization]);

  // ============================================================
  // SUBSCRIPTION HOOK
  // ============================================================

  const {
    loading: subscriptionActionLoading,

    error: subscriptionActionError,

    renew,

    changePlan,

    start,

    cancel,

    clearError: clearSubscriptionError,

    history,

    historyLoading,

    historyError,

    loadHistory,

    clearHistoryError,
  } = useOrganizationSubscription({
    organizationId,

    onSuccess: refreshOrganization,
  });

  // ============================================================
  // OPEN SUBSCRIPTION HISTORY
  // ============================================================

  const handleOpenHistory = async () => {
    clearSubscriptionError();

    clearHistoryError();

    setSubscriptionHistoryOpen(true);

    await loadHistory();
  };

  // ============================================================
  // OPEN RENEW
  // ============================================================

  const handleOpenRenew = () => {
    clearSubscriptionError();

    setRenewOpen(true);
  };

  // ============================================================
  // OPEN CHANGE PLAN
  // ============================================================

  const handleOpenChangePlan = async () => {
    clearSubscriptionError();

    if (activePlans.length === 0) {
      await loadActivePlans();
    }

    setChangePlanOpen(true);
  };

  // ============================================================
  // OPEN START SUBSCRIPTION
  // ============================================================

  const handleOpenStartSubscription = async () => {
    clearSubscriptionError();

    if (activePlans.length === 0) {
      await loadActivePlans();
    }

    setStartSubscriptionOpen(true);
  };

  // ============================================================
  // OPEN CANCEL
  // ============================================================

  const handleOpenCancel = () => {
    clearSubscriptionError();

    setCancelSubscriptionOpen(true);
  };

  // ============================================================
  // RENEW
  // ============================================================

  const handleRenew = async ({ billingCycle }) => {
    const response = await renew({
      billingCycle,
    });

    if (response) {
      setRenewOpen(false);
    }
  };

  // ============================================================
  // CHANGE PLAN
  // ============================================================

  const handleChangePlan = async ({ plan, billingCycle }) => {
    const response = await changePlan({
      plan,
      billingCycle,
    });

    if (response) {
      setChangePlanOpen(false);
    }
  };

  // ============================================================
  // START SUBSCRIPTION
  // ============================================================

  const handleStartSubscription = async ({ plan, billingCycle }) => {
    const response = await start({
      plan,
      billingCycle,
    });

    if (response) {
      setStartSubscriptionOpen(false);
    }
  };

  // ============================================================
  // CANCEL SUBSCRIPTION
  // ============================================================

  const handleCancelSubscription = async () => {
    const response = await cancel();

    if (response) {
      setCancelSubscriptionOpen(false);
    }
  };

  // ============================================================
  // DELETE ORGANIZATION
  // ============================================================

  const handleDelete = async () => {
    if (!organizationId || deleting) {
      return;
    }

    try {
      setDeleting(true);
      setError(null);

      const response =
        await organizationService.deleteOrganization(organizationId);

      if (!response?.success) {
        throw new Error(response?.message || "Unable to delete organization.");
      }

      setDeleteOpen(false);

      navigate("/organizations");
    } catch (error) {
      console.error("Failed to delete organization:", error);

      setError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to delete organization. Please try again.",
      );
    } finally {
      setDeleting(false);
    }
  };

  // ============================================================
  // CONNECT SOCIAL ACCOUNT
  // ============================================================

  const handleSocialConnect = async (platform, selectedOrganizationId) => {
    if (!selectedOrganizationId || selectedOrganizationId !== organizationId) {
      setSocialConnectError("Organization is required.");

      return;
    }

    // ========================================================
    // META
    // ========================================================

    if (platform === "meta") {
      try {
        setSocialConnectError("");
        setSocialConnectSuccess("");

        setConnectingPlatform("meta");

        await metaService.startOAuth(selectedOrganizationId);
      } catch (error) {
        console.error("Failed to start Meta OAuth:", error);

        setConnectingPlatform(null);

        setSocialConnectError(
          error?.response?.data?.message ||
            error?.message ||
            "Unable to start Meta connection. Please try again.",
        );
      }

      return;
    }

    // ========================================================
    // LINKEDIN
    // ========================================================

    if (platform === "linkedin") {
      setSocialConnectError("LinkedIn integration is coming soon.");

      return;
    }

    // ========================================================
    // YOUTUBE
    // ========================================================

    if (platform === "youtube") {
      setSocialConnectError("YouTube integration is coming soon.");

      return;
    }

    // ========================================================
    // UNKNOWN
    // ========================================================

    setSocialConnectError("This social platform is not available yet.");
  };

  // ============================================================
  // INITIAL LOADING
  // ============================================================

  if (loading) {
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
  // ORGANIZATION LOAD ERROR
  // ============================================================

  if (error || !organization) {
    return (
      <Box
        sx={{
          maxWidth: 980,
          mx: "auto",
          p: 3,
        }}
      >
        <Alert severity="error">{error || "Organization not found."}</Alert>
      </Box>
    );
  }

  // ============================================================
  // SUBSCRIPTION STATE
  // ============================================================

  const hasCurrentSubscription = Boolean(organization.subscription_status);

  const isSubscriptionActive = organization.subscription_status === "active";

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <>
      {/* ======================================================
          HEADER
      ====================================================== */}

      <OverviewHeader
        organization={organization}
        onEdit={() => navigate(`/organizations/${organizationId}/edit`)}
        onDelete={() => setDeleteOpen(true)}
      />

      {/* ======================================================
          PAGE LEVEL SUBSCRIPTION ERROR
      ====================================================== */}

      {(subscriptionActionError || plansError) && (
        <Alert
          severity="error"
          sx={{
            mb: 3,
            borderRadius: "12px",
          }}
        >
          {subscriptionActionError || plansError}
        </Alert>
      )}

      {/* ======================================================
          SOCIAL CONNECT ERROR
      ====================================================== */}

      {socialConnectError && (
        <Alert
          severity="error"
          sx={{
            mb: 3,
            borderRadius: "12px",
          }}
          onClose={() => setSocialConnectError("")}
        >
          {socialConnectError}
        </Alert>
      )}

      {/* ======================================================
          OVERVIEW
      ====================================================== */}

      <OverviewLayout
        brandInformation={<BrandInformationCard organization={organization} />}
        contactInformation={
          <ContactInformationCard organization={organization} />
        }
        socialAccounts={
          <SocialAccountsSection
            organizationId={organizationId}
            onConnect={handleSocialConnect}
            connectingPlatform={connectingPlatform}
            refreshKey={socialAccountsRefreshKey}
          />
        }
        activityTimeline={<ActivityTimelineCard organization={organization} />}
        profile={<OrganizationProfileCard organization={organization} />}
        subscription={
          <SubscriptionCard
            organization={organization}
            onRenew={handleOpenRenew}
            onChangePlan={
              isSubscriptionActive ? handleOpenChangePlan : undefined
            }
            onCancel={isSubscriptionActive ? handleOpenCancel : undefined}
            onStartSubscription={
              !hasCurrentSubscription ? handleOpenStartSubscription : undefined
            }
            onViewHistory={handleOpenHistory}
            actionLoading={subscriptionActionLoading}
          />
        }
      />

      {/* ======================================================
          META PAGE SELECTION
      ====================================================== */}

      <MetaPageSelectionDialog
        open={metaSelectionOpen}
        pages={metaSelectionPages}
        loading={metaSelectionLoading}
        submitting={metaSelectionSubmitting}
        error={metaSelectionError}
        onClose={() => {
          if (metaSelectionSubmitting) {
            return;
          }

          setMetaSelectionOpen(false);

          setMetaSelectionPages([]);

          setMetaSelectionKey("");

          setMetaSelectionError("");

          setConnectingPlatform(null);
        }}
        onConfirm={handleMetaPageSelection}
      />

      {/* ======================================================
          DELETE
      ====================================================== */}

      <ConfirmDialog
        open={deleteOpen}
        title="Delete organization"
        message="Are you sure you want to delete"
        entityName={organization.name}
        description="This will also remove its social accounts, posts, and campaigns. This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        loading={deleting}
        onClose={() => {
          if (!deleting) {
            setDeleteOpen(false);
          }
        }}
        onConfirm={handleDelete}
      />

      {/* ======================================================
          RENEW
      ====================================================== */}

      <RenewSubscriptionDialog
        open={renewOpen}
        organization={organization}
        loading={subscriptionActionLoading}
        error={subscriptionActionError}
        onClose={() => {
          if (!subscriptionActionLoading) {
            setRenewOpen(false);

            clearSubscriptionError();
          }
        }}
        onSubmit={handleRenew}
      />

      {/* ======================================================
          CHANGE PLAN
      ====================================================== */}

      <ChangePlanDialog
        open={changePlanOpen}
        organization={organization}
        plans={activePlans}
        loading={subscriptionActionLoading || plansLoading}
        error={subscriptionActionError || plansError}
        onClose={() => {
          if (!subscriptionActionLoading) {
            setChangePlanOpen(false);

            clearSubscriptionError();
          }
        }}
        onSubmit={handleChangePlan}
      />

      {/* ======================================================
          START SUBSCRIPTION
      ====================================================== */}

      <StartSubscriptionDialog
        open={startSubscriptionOpen}
        plans={activePlans}
        loading={subscriptionActionLoading || plansLoading}
        error={subscriptionActionError || plansError}
        onClose={() => {
          if (!subscriptionActionLoading) {
            setStartSubscriptionOpen(false);

            clearSubscriptionError();
          }
        }}
        onSubmit={handleStartSubscription}
      />

      {/* ======================================================
          CANCEL
      ====================================================== */}

      <CancelSubscriptionDialog
        open={cancelSubscriptionOpen}
        organization={organization}
        loading={subscriptionActionLoading}
        error={subscriptionActionError}
        onClose={() => {
          if (!subscriptionActionLoading) {
            setCancelSubscriptionOpen(false);

            clearSubscriptionError();
          }
        }}
        onConfirm={handleCancelSubscription}
      />

      {/* ======================================================
          HISTORY
      ====================================================== */}

      <SubscriptionHistoryDrawer
        open={subscriptionHistoryOpen}
        onClose={() => {
          if (!historyLoading) {
            setSubscriptionHistoryOpen(false);

            clearHistoryError();
          }
        }}
        subscriptions={history}
        loading={historyLoading}
        error={historyError}
      />

      {/* ======================================================
          SUCCESS
      ====================================================== */}

      <Snackbar
        open={Boolean(socialConnectSuccess)}
        autoHideDuration={5000}
        onClose={() => setSocialConnectSuccess("")}
        anchorOrigin={{
          vertical: "top",
          horizontal: "right",
        }}
      >
        <Alert
          severity="success"
          variant="filled"
          onClose={() => setSocialConnectSuccess("")}
        >
          {socialConnectSuccess}
        </Alert>
      </Snackbar>
    </>
  );
}
