import { useEffect, useMemo } from "react";

import { Alert, Box, Grid, Stack, Typography } from "@mui/material";

import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

import { useFormContext } from "react-hook-form";

import SectionCard from "./SectionCard";
import SocialAccountCard from "./SocialAccountCard";

import { PLATFORM_IDS } from "../../../constants/platforms/platformCapabilities";

import { getPlatformStates } from "../../../utils/post/platformCapability.utils";

import { TYPOGRAPHY } from "../../../theme/typography";

// ============================================================
// SUPPORTED PLATFORMS
// ============================================================

const SUPPORTED_PLATFORM_IDS = new Set([
  PLATFORM_IDS.INSTAGRAM,
  PLATFORM_IDS.FACEBOOK,
  PLATFORM_IDS.LINKEDIN,
  PLATFORM_IDS.YOUTUBE,
]);

// ============================================================
// PLATFORM ORDER
// ============================================================

const PLATFORM_ORDER = [
  PLATFORM_IDS.INSTAGRAM,
  PLATFORM_IDS.FACEBOOK,
  PLATFORM_IDS.LINKEDIN,
  PLATFORM_IDS.YOUTUBE,
];

// ============================================================
// PLATFORM LABELS
// ============================================================

const PLATFORM_LABELS = {
  [PLATFORM_IDS.INSTAGRAM]: "Instagram",
  [PLATFORM_IDS.FACEBOOK]: "Facebook",
  [PLATFORM_IDS.LINKEDIN]: "LinkedIn",
  [PLATFORM_IDS.YOUTUBE]: "YouTube",
};

// ============================================================
// COMPONENT
// ============================================================

export default function PlatformSection({ platforms = [], accounts = [] }) {
  const {
    watch,
    setValue,
    clearErrors,
    formState: { errors },
  } = useFormContext();

  // ==========================================================
  // FORM STATE
  // ==========================================================

  const organizationId = watch("organization") || "";

  const selectedPlatforms = watch("platforms") || [];

  const selectedAccountIds = watch("social_account_ids") || [];

  const platformContentTypes = watch("platform_content_types") || {};

  const media = watch("media") || [];

  // ==========================================================
  // PLATFORM CAPABILITY MAP
  // ==========================================================

  const capabilityMap = useMemo(() => {
    const states = getPlatformStates({
      media,
    });

    return new Map(states.map((item) => [item.platform, item]));
  }, [media]);

  // ==========================================================
  // PLATFORM DEFINITIONS
  // ==========================================================

  const platformMap = useMemo(() => {
    return new Map(
      platforms
        .filter((platform) => SUPPORTED_PLATFORM_IDS.has(platform?.id))
        .map((platform) => [platform.id, platform]),
    );
  }, [platforms]);

  // ==========================================================
  // ORGANIZATION ACCOUNTS
  // ==========================================================

  const organizationAccounts = useMemo(() => {
    if (!organizationId || !Array.isArray(accounts)) {
      return [];
    }

    return accounts
      .filter(
        (account) =>
          account?.organizationId === organizationId &&
          SUPPORTED_PLATFORM_IDS.has(account?.platform) &&
          account?.connected !== false,
      )
      .sort((a, b) => {
        const platformA = PLATFORM_ORDER.indexOf(a?.platform);

        const platformB = PLATFORM_ORDER.indexOf(b?.platform);

        if (platformA !== platformB) {
          return platformA - platformB;
        }

        const nameA = a?.accountName || a?.pageName || a?.username || "";

        const nameB = b?.accountName || b?.pageName || b?.username || "";

        return nameA.localeCompare(nameB);
      });
  }, [accounts, organizationId]);

  // ==========================================================
  // GROUP ACCOUNTS BY PLATFORM
  // ==========================================================

  const accountsByPlatform = useMemo(() => {
    const grouped = new Map();

    organizationAccounts.forEach((account) => {
      const platformId = account?.platform;

      if (!grouped.has(platformId)) {
        grouped.set(platformId, []);
      }

      grouped.get(platformId).push(account);
    });

    return grouped;
  }, [organizationAccounts]);

  // ==========================================================
  // DISPLAY PLATFORMS
  // ==========================================================

  const accountPlatforms = useMemo(() => {
    return PLATFORM_ORDER.filter((platformId) =>
      accountsByPlatform.has(platformId),
    );
  }, [accountsByPlatform]);

  // ==========================================================
  // SYNCHRONIZE DERIVED FORM STATE
  // ==========================================================
  //
  // `social_account_ids` is the actual publishing destination.
  //
  // `platforms` is derived from the selected accounts and is
  // retained for the existing content-type/capability system.
  //
  // IMPORTANT:
  // These updates intentionally do NOT validate immediately.
  // Content-type validation should happen when the user submits
  // the form, not while they are still selecting accounts.
  // ==========================================================

  useEffect(() => {
    const validAccountIds = new Set(
      organizationAccounts
        .filter((account) => {
          const capability = capabilityMap.get(account?.platform);

          return (
            capability?.available &&
            account?.connected !== false &&
            account?.valid !== false
          );
        })
        .map((account) => account?.id)
        .filter(Boolean),
    );

    const currentAccountIds = Array.isArray(selectedAccountIds)
      ? selectedAccountIds
      : [];

    const cleanedAccountIds = currentAccountIds.filter((accountId) =>
      validAccountIds.has(accountId),
    );

    const accountIdsChanged =
      cleanedAccountIds.length !== currentAccountIds.length ||
      cleanedAccountIds.some(
        (accountId, index) => accountId !== currentAccountIds[index],
      );

    if (accountIdsChanged) {
      setValue("social_account_ids", cleanedAccountIds, {
        shouldDirty: true,
        shouldValidate: false,
      });
    }

    // ----------------------------------------------------------
    // DERIVE PLATFORMS
    // ----------------------------------------------------------

    const nextPlatforms = [
      ...new Set(
        organizationAccounts
          .filter((account) => cleanedAccountIds.includes(account?.id))
          .map((account) => account?.platform)
          .filter(Boolean),
      ),
    ];

    const platformsChanged =
      nextPlatforms.length !== selectedPlatforms.length ||
      nextPlatforms.some(
        (platformId, index) => platformId !== selectedPlatforms[index],
      );

    if (platformsChanged) {
      setValue("platforms", nextPlatforms, {
        shouldDirty: true,
        shouldValidate: false,
      });
    }

    // ----------------------------------------------------------
    // REMOVE CONTENT TYPES FOR REMOVED PLATFORMS
    // ----------------------------------------------------------

    const nextContentTypes = {
      ...platformContentTypes,
    };

    Object.keys(nextContentTypes).forEach((platformId) => {
      if (!nextPlatforms.includes(platformId)) {
        delete nextContentTypes[platformId];
      }
    });

    const contentTypesChanged =
      Object.keys(nextContentTypes).length !==
        Object.keys(platformContentTypes).length ||
      Object.keys(nextContentTypes).some(
        (platformId) =>
          nextContentTypes[platformId] !== platformContentTypes[platformId],
      );

    if (contentTypesChanged) {
      setValue("platform_content_types", nextContentTypes, {
        shouldDirty: true,
        shouldValidate: false,
      });
    }
  }, [
    organizationAccounts,
    capabilityMap,
    selectedAccountIds,
    selectedPlatforms,
    platformContentTypes,
    setValue,
  ]);

  // ==========================================================
  // ACCOUNT TOGGLE
  // ==========================================================

  function toggleAccount(account) {
    if (!account?.id) {
      return;
    }

    const capability = capabilityMap.get(account.platform);

    // ----------------------------------------------------------
    // MEDIA REQUIRED
    // ----------------------------------------------------------

    if (!media.length) {
      return;
    }

    // ----------------------------------------------------------
    // PLATFORM MUST SUPPORT MEDIA
    // ----------------------------------------------------------

    if (!capability?.available) {
      return;
    }

    // ----------------------------------------------------------
    // ACCOUNT MUST BE VALID
    // ----------------------------------------------------------

    if (account?.connected === false || account?.valid === false) {
      return;
    }

    const isSelected = selectedAccountIds.includes(account.id);

    const nextAccountIds = isSelected
      ? selectedAccountIds.filter((id) => id !== account.id)
      : [...selectedAccountIds, account.id];

    // ----------------------------------------------------------
    // ACCOUNT IDS
    // ----------------------------------------------------------

    setValue("social_account_ids", nextAccountIds, {
      shouldDirty: true,
      shouldValidate: false,
    });

    // ----------------------------------------------------------
    // DERIVE PLATFORMS
    // ----------------------------------------------------------

    const nextPlatforms = [
      ...new Set(
        organizationAccounts
          .filter((accountItem) => nextAccountIds.includes(accountItem?.id))
          .map((accountItem) => accountItem?.platform)
          .filter(Boolean),
      ),
    ];

    setValue("platforms", nextPlatforms, {
      shouldDirty: true,
      shouldValidate: false,
    });

    // ----------------------------------------------------------
    // CLEAN CONTENT TYPES
    // ----------------------------------------------------------

    const nextContentTypes = {
      ...platformContentTypes,
    };

    Object.keys(nextContentTypes).forEach((platformId) => {
      if (!nextPlatforms.includes(platformId)) {
        delete nextContentTypes[platformId];
      }
    });

    setValue("platform_content_types", nextContentTypes, {
      shouldDirty: true,
      shouldValidate: false,
    });

    // ----------------------------------------------------------
    // CLEAR DOWNSTREAM VALIDATION
    // ----------------------------------------------------------
    //
    // If the user previously submitted the form and errors were
    // visible, changing the publishing accounts should not keep
    // stale content-type/platform errors on screen.
    //
    // Fresh validation will happen again on submit.
    // ----------------------------------------------------------

    clearErrors(["platforms", "social_account_ids", "platform_content_types"]);
  }

  // ==========================================================
  // ORGANIZATION NOT SELECTED
  // ==========================================================

  if (!organizationId) {
    return (
      <SectionCard
        title="Publishing Accounts"
        description="Choose the accounts where this post will be published."
      >
        <Alert
          severity="info"
          icon={<InfoOutlinedIcon />}
          sx={{
            borderRadius: 2,
            fontSize: 13,
          }}
        >
          Select an organization to view its connected social accounts.
        </Alert>
      </SectionCard>
    );
  }

  // ==========================================================
  // NO CONNECTED ACCOUNTS
  // ==========================================================

  if (!organizationAccounts.length) {
    return (
      <SectionCard
        title="Publishing Accounts"
        description="Choose the accounts where this post will be published."
      >
        <Alert
          severity="info"
          icon={<InfoOutlinedIcon />}
          sx={{
            borderRadius: 2,
            fontSize: 13,
          }}
        >
          No connected social accounts are available for this organization.
        </Alert>
      </SectionCard>
    );
  }

  // ==========================================================
  // UNSUPPORTED PLATFORMS
  // ==========================================================

  const unsupportedPlatforms =
    media.length > 0
      ? accountPlatforms.filter(
          (platformId) => !capabilityMap.get(platformId)?.available,
        )
      : [];

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <SectionCard
      title="Publishing Accounts"
      description="Choose the accounts where this post will be published."
    >
      <Stack spacing={3}>
        {/* ====================================================
            MEDIA REQUIRED
        ==================================================== */}

        {!media.length && (
          <Alert
            severity="info"
            icon={<InfoOutlinedIcon />}
            sx={{
              borderRadius: 2,
              fontSize: 13,
              py: 0.5,
            }}
          >
            Upload media to choose publishing accounts.
          </Alert>
        )}

        {/* ====================================================
            UNSUPPORTED PLATFORM
        ==================================================== */}

        {unsupportedPlatforms.length > 0 && (
          <Alert
            severity="info"
            icon={<InfoOutlinedIcon />}
            sx={{
              borderRadius: 2,
              fontSize: 13,
              py: 0.5,
            }}
          >
            Selected media isn't supported on{" "}
            {unsupportedPlatforms
              .map((platformId) => PLATFORM_LABELS[platformId] || platformId)
              .join(", ")}
            .
          </Alert>
        )}

        {/* ====================================================
            PLATFORM GROUPS
        ==================================================== */}

        {accountPlatforms.map((platformId) => {
          const platformAccounts = accountsByPlatform.get(platformId) || [];

          const platform = platformMap.get(platformId);

          const capability = capabilityMap.get(platformId);

          const isAvailable =
            media.length > 0 && Boolean(capability?.available);

          const platformName =
            platform?.name || PLATFORM_LABELS[platformId] || platformId;

          return (
            <Box key={platformId}>
              {/* ==========================================
                    PLATFORM HEADER
                ========================================== */}

              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 2,
                  mb: 1.25,
                }}
              >
                <Typography
                  component="h3"
                  sx={{
                    fontSize: 14,
                    fontWeight: 700,
                    color: "text.primary",
                    lineHeight: 1.4,
                  }}
                >
                  {platformName}
                </Typography>

                <Typography
                  sx={{
                    flexShrink: 0,
                    fontSize: 11.5,
                    color:
                      !media.length || !isAvailable
                        ? "text.disabled"
                        : "text.secondary",
                  }}
                >
                  {platformAccounts.length}{" "}
                  {platformAccounts.length === 1 ? "account" : "accounts"}
                </Typography>
              </Box>

              {/* ==========================================
                    ACCOUNT GRID
                ========================================== */}

              <Grid container spacing={1.5}>
                {platformAccounts.map((account) => {
                  const selected = selectedAccountIds.includes(account.id);

                  const disabled =
                    !media.length ||
                    !isAvailable ||
                    account?.connected === false ||
                    account?.valid === false;

                  return (
                    <Grid
                      key={account.id}
                      size={{
                        xs: 12,
                        sm: 6,
                        md: 4,
                      }}
                    >
                      <SocialAccountCard
                        account={account}
                        selected={selected}
                        disabled={disabled}
                        statusText=""
                        onChange={() => toggleAccount(account)}
                      />
                    </Grid>
                  );
                })}
              </Grid>
            </Box>
          );
        })}

        {/* ====================================================
            VALIDATION ERROR
        ==================================================== */}

        {errors?.social_account_ids && (
          <Typography
            sx={{
              ...TYPOGRAPHY.helperText,
              color: "error.main",
            }}
          >
            {errors.social_account_ids.message}
          </Typography>
        )}
      </Stack>
    </SectionCard>
  );
}
