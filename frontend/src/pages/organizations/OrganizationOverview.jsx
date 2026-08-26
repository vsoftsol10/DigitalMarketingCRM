// import { Alert, Box, CircularProgress } from "@mui/material";

// import { useCallback, useEffect, useState } from "react";

// import { useNavigate, useParams } from "react-router-dom";

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
//             variant="card"
//           />
//         }
//         activityTimeline={<ActivityTimelineCard organization={organization} />}
//         profile={<OrganizationProfileCard organization={organization} />}
//         subscription={
//           <SubscriptionCard
//             organization={organization}
//             onRenew={isSubscriptionActive ? handleOpenRenew : undefined}
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
//     </>
//   );
// }

import { Alert, Box, CircularProgress } from "@mui/material";

import { useCallback, useEffect, useState } from "react";

import { useNavigate, useParams } from "react-router-dom";

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

// ============================================================
// TEMPORARY DUMMY SOCIAL ACCOUNTS
// ============================================================
//
// UI development only.
//
// This allows us to preview connected social accounts
// before real OAuth/backend integration is implemented.
//
// Later, remove:
//   1. This import
//   2. accounts={DEMO_SOCIAL_ACCOUNTS}
//
// Then SocialAccountsSection will use the real backend.
// ============================================================

import { DEMO_SOCIAL_ACCOUNTS } from "../../constants/social/socialAccountDummyData";

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
  // LOAD ORGANIZATION ON MOUNT / ID CHANGE
  // ============================================================

  useEffect(() => {
    loadOrganization();
  }, [loadOrganization]);

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
  // RENEW SUBSCRIPTION
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
          OVERVIEW LAYOUT
      ====================================================== */}

      <OverviewLayout
        brandInformation={<BrandInformationCard organization={organization} />}
        contactInformation={
          <ContactInformationCard organization={organization} />
        }
        socialAccounts={
          <SocialAccountsSection
            organizationId={organizationId}
            accounts={DEMO_SOCIAL_ACCOUNTS}
          />
        }
        activityTimeline={<ActivityTimelineCard organization={organization} />}
        profile={<OrganizationProfileCard organization={organization} />}
        subscription={
          <SubscriptionCard
            organization={organization}
            onRenew={isSubscriptionActive ? handleOpenRenew : undefined}
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
          DELETE ORGANIZATION
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
          RENEW SUBSCRIPTION
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
          CANCEL SUBSCRIPTION
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
          SUBSCRIPTION HISTORY
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
    </>
  );
}
