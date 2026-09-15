import { Alert, Box, CircularProgress, Snackbar } from "@mui/material";

import { useCallback, useEffect, useState } from "react";

import { useNavigate, useParams } from "react-router-dom";

import metaService from "../../services/social/meta.service";
import instagramService from "../../services/social/instagram.service";

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

import useSocialAccounts from "../../hooks/social/useSocialAccounts";
// ============================================================
// SERVICES
// ============================================================

import organizationService from "../../services/organization/organization.service";
import plansService from "../../services/plans.service";

import ConnectSocialAccountDialog from "../../components/organization/social/ConnectSocialAccountDialog";

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
  // SOCIAL DISCONNECT STATE
  // ============================================================

  const [socialDisconnectOpen, setSocialDisconnectOpen] = useState(false);

  const [socialAccountToDisconnect, setSocialAccountToDisconnect] =
    useState(null);

  const [socialDisconnectLoading, setSocialDisconnectLoading] = useState(false);

  // ============================================================
  // FACEBOOK PAGE SELECTION STATE
  // ============================================================

  const [facebookSelectionOpen, setFacebookSelectionOpen] = useState(false);

  const [facebookSelectionLoading, setFacebookSelectionLoading] =
    useState(false);

  const [facebookSelectionSubmitting, setFacebookSelectionSubmitting] =
    useState(false);

  const [facebookSelectionError, setFacebookSelectionError] = useState("");

  const [facebookSelectionPages, setFacebookSelectionPages] = useState([]);

  const [facebookSelectionKey, setFacebookSelectionKey] = useState("");

  // ============================================================
  // SOCIAL ACCOUNTS REFRESH
  // ============================================================

  const [socialAccountsRefreshKey, setSocialAccountsRefreshKey] = useState(0);

  const [socialConnectDialogOpen, setSocialConnectDialogOpen] = useState(false);

  const [socialConnectDialogPlatform, setSocialConnectDialogPlatform] =
    useState(null);

  const [socialConnectDialogLoading, setSocialConnectDialogLoading] =
    useState(false);

  // ============================================================
  // SOCIAL RECONNECT DIALOG STATE
  // ============================================================

  const [socialReconnectDialogOpen, setSocialReconnectDialogOpen] =
    useState(false);

  const [socialReconnectAccount, setSocialReconnectAccount] = useState(null);

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

  const { disconnectAccount } = useSocialAccounts(organizationId);

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
  // LOAD FACEBOOK PAGE SELECTION
  // ============================================================

  const loadFacebookSelection = useCallback(
    async (selectionKey) => {
      if (!organizationId || !selectionKey) {
        setFacebookSelectionError("Facebook authorization session is missing.");

        setFacebookSelectionPages([]);
        setFacebookSelectionOpen(true);

        return;
      }

      try {
        setFacebookSelectionLoading(true);
        setFacebookSelectionError("");

        setFacebookSelectionKey(selectionKey);

        const response = await metaService.getOAuthSelection(
          organizationId,
          selectionKey,
        );

        const pages = Array.isArray(response?.data?.pages)
          ? response.data.pages
          : [];

        setFacebookSelectionPages(pages);

        setFacebookSelectionOpen(true);
      } catch (error) {
        console.error("Failed to load Facebook Page selection:", error);

        setFacebookSelectionError(
          error?.response?.data?.message ||
            error?.message ||
            "Unable to load Facebook Pages.",
        );

        setFacebookSelectionPages([]);

        setFacebookSelectionOpen(true);
      } finally {
        setFacebookSelectionLoading(false);
      }
    },
    [organizationId],
  );

  // ============================================================
  // HANDLE FACEBOOK PAGE SELECTION
  // ============================================================

  const handleFacebookPageSelection = useCallback(
    async (pageId) => {
      if (
        !organizationId ||
        !facebookSelectionKey ||
        !pageId ||
        facebookSelectionSubmitting
      ) {
        return;
      }

      try {
        setFacebookSelectionSubmitting(true);
        setFacebookSelectionError("");

        const response = await metaService.confirmOAuthSelection(
          organizationId,
          facebookSelectionKey,
          pageId,
        );

        const data = response?.data || {};

        const count = Number(data.accounts_connected || 0);

        setFacebookSelectionOpen(false);

        setFacebookSelectionPages([]);

        setFacebookSelectionKey("");

        setConnectingPlatform(null);

        showSuccess(
          count > 0
            ? `${count} Facebook Page(s) connected successfully.`
            : "Facebook Page connected successfully.",
        );

        refreshSocialAccounts();
      } catch (error) {
        console.error("Failed to confirm Facebook Page selection:", error);

        setFacebookSelectionError(
          error?.response?.data?.message ||
            error?.message ||
            "Unable to connect the selected Facebook Page.",
        );
      } finally {
        setFacebookSelectionSubmitting(false);
      }
    },
    [
      organizationId,
      facebookSelectionKey,
      facebookSelectionSubmitting,
      refreshSocialAccounts,
      showSuccess,
    ],
  );

  // ============================================================
  // HANDLE SOCIAL OAUTH CALLBACK
  // ============================================================

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);

    // ==========================================================
    // FACEBOOK / META CALLBACK PARAMETERS
    // ==========================================================

    const socialConnect = params.get("social_connect");

    const platform = params.get("platform");

    const accountsConnected = params.get("accounts_connected");

    const reason = params.get("reason");

    const selectionKey = params.get("selection_key");

    // ==========================================================
    // INSTAGRAM CALLBACK PARAMETERS
    // ==========================================================

    const instagramOAuth = params.get("instagram_oauth");

    const instagramSocialAccountId = params.get("social_account_id");

    const instagramMessage = params.get("message");

    // ==========================================================
    // NOTHING TO HANDLE
    // ==========================================================

    if (!socialConnect && !instagramOAuth) {
      return;
    }

    // ==========================================================
    // FACEBOOK - SELECTION REQUIRED
    // ==========================================================

    if (socialConnect === "selection" && platform === "meta") {
      setConnectingPlatform("facebook");

      loadFacebookSelection(selectionKey);
    }

    // ==========================================================
    // FACEBOOK - SUCCESS
    // ==========================================================

    if (socialConnect === "success" && platform === "meta") {
      setConnectingPlatform(null);

      const count = Number(accountsConnected || 0);

      showSuccess(
        count > 0
          ? `${count} Facebook Page(s) connected successfully.`
          : "Facebook Page connected successfully.",
      );

      refreshSocialAccounts();
    }

    // ==========================================================
    // FACEBOOK - ERROR
    // ==========================================================

    if (socialConnect === "error" && (!platform || platform === "meta")) {
      setConnectingPlatform(null);

      showError(reason || "Unable to connect Facebook Page. Please try again.");
    }

    // ==========================================================
    // INSTAGRAM - SUCCESS
    // ==========================================================

    if (instagramOAuth === "success") {
      setConnectingPlatform(null);

      showSuccess(
        instagramSocialAccountId
          ? "Instagram account connected successfully."
          : "Instagram account connected successfully.",
      );

      refreshSocialAccounts();
    }

    // ==========================================================
    // INSTAGRAM - ERROR
    // ==========================================================

    if (instagramOAuth === "error") {
      setConnectingPlatform(null);

      showError(
        instagramMessage ||
          reason ||
          "Unable to connect Instagram account. Please try again.",
      );
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

    params.delete("instagram_oauth");
    params.delete("social_account_id");
    params.delete("message");

    const queryString = params.toString();

    const cleanUrl =
      `${window.location.pathname}` + `${queryString ? `?${queryString}` : ""}`;

    window.history.replaceState({}, document.title, cleanUrl);
  }, [loadFacebookSelection, refreshSocialAccounts, showError, showSuccess]);

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

  // ============================================================
  // CONNECT SOCIAL ACCOUNT
  // ============================================================

  const handleSocialConnect = (platform, selectedOrganizationId) => {
    if (!selectedOrganizationId || selectedOrganizationId !== organizationId) {
      setSocialConnectError("Organization is required.");

      return;
    }

    if (platform === "facebook" || platform === "instagram") {
      setSocialConnectError("");
      setSocialConnectSuccess("");

      setSocialConnectDialogPlatform(platform);
      setSocialConnectDialogOpen(true);

      return;
    }

    if (platform === "meta") {
      setSocialConnectError("");
      setSocialConnectSuccess("");

      setSocialConnectDialogPlatform("facebook");
      setSocialConnectDialogOpen(true);

      return;
    }

    if (platform === "linkedin") {
      setSocialConnectError("LinkedIn integration is coming soon.");

      return;
    }

    if (platform === "youtube") {
      setSocialConnectError("YouTube integration is coming soon.");

      return;
    }

    setSocialConnectError("This social platform is not available yet.");
  };
  // ============================================================
  // HANDLE SOCIAL DISCONNECT
  // ============================================================

  const handleSocialDisconnect = useCallback((account) => {
    if (!account?.id) {
      return;
    }

    setSocialAccountToDisconnect(account);
    setSocialDisconnectOpen(true);
  }, []);

  // ============================================================
  // CONFIRM SOCIAL DISCONNECT
  // ============================================================

  const handleConfirmSocialDisconnect = useCallback(async () => {
    if (!socialAccountToDisconnect?.id || socialDisconnectLoading) {
      return;
    }

    try {
      setSocialDisconnectLoading(true);

      await disconnectAccount(socialAccountToDisconnect.id);

      setSocialDisconnectOpen(false);
      setSocialAccountToDisconnect(null);

      showSuccess("Social account disconnected successfully.");

      refreshSocialAccounts();
    } catch (error) {
      console.error("Failed to disconnect social account:", error);

      showError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to disconnect social account. Please try again.",
      );
    } finally {
      setSocialDisconnectLoading(false);
    }
  }, [
    socialAccountToDisconnect,
    socialDisconnectLoading,
    disconnectAccount,
    refreshSocialAccounts,
    showSuccess,
    showError,
  ]);
  const handleContinueSocialConnect = async (platform) => {
    if (!organizationId) {
      return;
    }

    try {
      setSocialConnectDialogLoading(true);

      if (platform === "facebook") {
        await metaService.startOAuth(organizationId);
        return;
      }

      if (platform === "instagram") {
        await instagramService.startOAuth(organizationId);
        return;
      }
    } catch (error) {
      console.error("Failed to start social OAuth:", error);
      setSocialConnectDialogLoading(false);
    }
  };

  // ============================================================
  // OPEN SOCIAL RECONNECT
  // ============================================================

  const handleSocialReconnect = useCallback(
    (account) => {
      if (!account?.id || !account?.platform) {
        return;
      }

      if (account.platform !== "facebook" && account.platform !== "instagram") {
        showError("Reconnect is not available for this social platform.");
        return;
      }

      setSocialConnectError("");
      setSocialConnectSuccess("");

      setSocialReconnectAccount(account);
      setSocialReconnectDialogOpen(true);
    },
    [showError],
  );

  // ============================================================
  // CONTINUE SOCIAL RECONNECT
  // ============================================================

  const handleContinueSocialReconnect = async (platform) => {
    if (!organizationId) {
      return;
    }

    try {
      setSocialConnectDialogLoading(true);

      if (platform === "facebook") {
        await metaService.startOAuth(organizationId);
        return;
      }

      if (platform === "instagram") {
        await instagramService.startOAuth(organizationId);
        return;
      }

      setSocialConnectDialogLoading(false);

      setSocialReconnectDialogOpen(false);
      setSocialReconnectAccount(null);

      showError("Reconnect is not available for this social platform.");
    } catch (error) {
      console.error("Failed to start social reconnect:", error);

      setSocialConnectDialogLoading(false);

      showError(
        error?.response?.data?.message ||
          error?.message ||
          "Failed to reconnect social account.",
      );
    }
  };

  // ============================================================
  // CLOSE SOCIAL RECONNECT DIALOG
  // ============================================================

  const handleCloseSocialReconnect = useCallback(() => {
    if (socialConnectDialogLoading) {
      return;
    }

    setSocialReconnectDialogOpen(false);
    setSocialReconnectAccount(null);
  }, [socialConnectDialogLoading]);
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
            onDisconnect={handleSocialDisconnect}
            onReconnect={handleSocialReconnect}
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
          FACEBOOK PAGE SELECTION
      ====================================================== */}

      <MetaPageSelectionDialog
        open={facebookSelectionOpen}
        pages={facebookSelectionPages}
        loading={facebookSelectionLoading}
        submitting={facebookSelectionSubmitting}
        error={facebookSelectionError}
        onClose={() => {
          if (facebookSelectionSubmitting) {
            return;
          }

          setFacebookSelectionOpen(false);

          setFacebookSelectionPages([]);

          setFacebookSelectionKey("");

          setFacebookSelectionError("");

          setConnectingPlatform(null);
        }}
        onConfirm={handleFacebookPageSelection}
      />

      <ConnectSocialAccountDialog
        isOpen={socialConnectDialogOpen}
        platform={socialConnectDialogPlatform}
        onClose={() => {
          if (socialConnectDialogLoading) {
            return;
          }

          setSocialConnectDialogOpen(false);
          setSocialConnectDialogPlatform(null);
        }}
        onContinue={handleContinueSocialConnect}
        isLoading={socialConnectDialogLoading}
      />

      <ConnectSocialAccountDialog
        isOpen={socialReconnectDialogOpen}
        platform={socialReconnectAccount?.platform || null}
        mode="reconnect"
        onClose={handleCloseSocialReconnect}
        onContinue={handleContinueSocialReconnect}
        isLoading={socialConnectDialogLoading}
      />

      <ConfirmDialog
        open={socialDisconnectOpen}
        title="Disconnect social account"
        message="Are you sure you want to disconnect"
        entityName={
          socialAccountToDisconnect?.pageName ||
          socialAccountToDisconnect?.username ||
          "this account"
        }
        description="You can reconnect this account later."
        confirmText="Disconnect"
        cancelText="Cancel"
        loading={socialDisconnectLoading}
        onClose={() => {
          if (socialDisconnectLoading) {
            return;
          }

          setSocialDisconnectOpen(false);
          setSocialAccountToDisconnect(null);
        }}
        onConfirm={handleConfirmSocialDisconnect}
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
