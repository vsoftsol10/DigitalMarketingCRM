import { FormProvider, useForm, useWatch } from "react-hook-form";

import { zodResolver } from "@hookform/resolvers/zod";

import toast from "react-hot-toast";

import { Box, Grid } from "@mui/material";

import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";

import { useQuery } from "@tanstack/react-query";

import postService from "../../services/post.service";
import organizationService from "../../services/organization/organization.service";
import socialAccountService from "../../services/social/socialAccount.service";

import OrganizationSection from "../../components/post/create/OrganizationSection";
import PlatformSection from "../../components/post/create/PlatformSection";
import ContentTypeSection from "../../components/post/create/ContentTypeSection";
import MediaUploadSection from "../../components/post/create/media/MediaUploadSection";
import AICaptionSection from "../../components/post/create/AICaptionSection";
import CaptionSection from "../../components/post/create/CaptionSection";

import LivePreviewSection from "../../components/post/create/LivePreviewSection";
import PublishingSection from "../../components/post/create/PublishingSection";

import { createPostDefaultValues } from "../../constants/forms/createPostDefaultValues";

import { createPostSchema } from "../../validation/createPost.schema";

import { buildCreatePostPayload } from "../../utils/post/createPostPayload";
import { getPlatformStates } from "../../utils/post/platformCapability.utils";

import { CREATE_POST } from "../../data/post";

export default function CreatePost() {
  const location = useLocation();
  const plannerPrefill = location.state?.plannerPrefill;
  const hasAppliedPlannerBasePrefill = useRef(false);
  const hasAppliedPlannerAccountsPrefill = useRef(false);
  // ============================================================
  // FORM
  // ============================================================

  const methods = useForm({
    defaultValues: createPostDefaultValues,

    resolver: zodResolver(createPostSchema),

    mode: "onSubmit",

    reValidateMode: "onChange",

    shouldFocusError: true,
  });

  const {
    handleSubmit,

    setValue,

    formState: { isSubmitting: formIsSubmitting },
  } = methods;

  // ============================================================
  // PAGE DATA
  // ============================================================

  const selectedOrganizationId = useWatch({
    control: methods.control,
    name: "organization",
  }) || "";

  const media = useWatch({
    control: methods.control,
    name: "media",
  }) || [];

  const {
    data: organizationsResponse,
    isLoading: isLoadingOrganizations,
    error: organizationsError,
  } = useQuery({
    queryKey: ["organization-options", "create-post"],
    queryFn: () => organizationService.getOrganizationOptions(),
  });

  const {
    data: socialAccountsResponse,
  } = useQuery({
    queryKey: ["organization-social-accounts", selectedOrganizationId],
    queryFn: ({ signal }) =>
      socialAccountService.getOrganizationSocialAccounts(selectedOrganizationId, {
        signal,
      }),
    enabled: Boolean(selectedOrganizationId),
  });

  const createPostData = CREATE_POST;

  const organizations = Array.isArray(organizationsResponse?.data?.items)
    ? organizationsResponse.data.items.map((organization) => ({
        id: organization.organization_id,
        name: organization.name,
      }))
    : [];

  const socialAccounts = Array.isArray(socialAccountsResponse?.data)
    ? socialAccountsResponse.data.map((account) => ({
        ...account,
        organizationId: selectedOrganizationId,
        platform: String(account.platform || "").toUpperCase(),
        accountName: account.pageName,
      }))
    : [];

  // ============================================================
  // CONTENT PLANNER PREFILL
  // ============================================================
  //
  // Planner only supplies draft form values. The existing Create Post form,
  // account loader, media rules, validation, and submit flow remain the
  // source of truth.

  useEffect(() => {
    if (
      hasAppliedPlannerBasePrefill.current ||
      !plannerPrefill ||
      !organizationsResponse?.success ||
      !organizations.some(
        (organization) => organization.id === plannerPrefill.organization,
      )
    ) {
      return;
    }

    setValue("organization", plannerPrefill.organization, {
      shouldDirty: false,
      shouldValidate: false,
    });
    setValue("caption", plannerPrefill.caption || "", {
      shouldDirty: false,
      shouldValidate: false,
    });
    setValue("publish_type", "SCHEDULE", {
      shouldDirty: false,
      shouldValidate: false,
    });
    setValue("publish_date", plannerPrefill.publishDate || "", {
      shouldDirty: false,
      shouldValidate: false,
    });
    setValue("publish_time", plannerPrefill.publishTime || "", {
      shouldDirty: false,
      shouldValidate: false,
    });
    hasAppliedPlannerBasePrefill.current = true;
  }, [organizations, organizationsResponse?.success, plannerPrefill, setValue]);

  useEffect(() => {
    if (
      hasAppliedPlannerAccountsPrefill.current ||
      !plannerPrefill ||
      selectedOrganizationId !== plannerPrefill.organization ||
      !Array.isArray(socialAccountsResponse?.data) ||
      !media.length
    ) {
      return;
    }

    const capabilityByPlatform = new Map(
      getPlatformStates({ media }).map((state) => [state.platform, state]),
    );
    const requestedAccountIds = Array.isArray(plannerPrefill.socialAccountIds)
      ? plannerPrefill.socialAccountIds
      : [];
    const availableAccounts = socialAccounts.filter(
      (account) => {
        const capability = capabilityByPlatform.get(account.platform);
        return (
          account.connected !== false &&
          account.valid !== false &&
          capability?.available
        );
      },
    );
    const selectedAccounts = availableAccounts.filter((account) =>
      requestedAccountIds.includes(account.id),
    );
    const selectedAccountIds = selectedAccounts.map((account) => account.id);
    const platforms = [...new Set(selectedAccounts.map((account) => account.platform))];
    const platformContentTypes = Object.fromEntries(
      platforms
        .filter((platform) =>
          capabilityByPlatform
            .get(platform)
            ?.contentTypes.some(
              (option) =>
                option.value === plannerPrefill.contentType && option.available,
            ),
        )
        .map((platform) => [platform, plannerPrefill.contentType]),
    );

    setValue("social_account_ids", selectedAccountIds, {
      shouldDirty: false,
      shouldValidate: false,
    });
    setValue("platforms", platforms, {
      shouldDirty: false,
      shouldValidate: false,
    });
    setValue("platform_content_types", platformContentTypes, {
      shouldDirty: false,
      shouldValidate: false,
    });
    hasAppliedPlannerAccountsPrefill.current = true;
  }, [
    media,
    plannerPrefill,
    selectedOrganizationId,
    setValue,
    socialAccounts,
    socialAccountsResponse?.data,
  ]);

  // ============================================================
  // SUBMIT STATE
  // ============================================================

  const [isSubmitting, setIsSubmitting] = useState(false);

  // ============================================================
  // SECTION REFS
  // ============================================================

  const sectionRefs = {
    organization: useRef(null),
    media: useRef(null),
    platforms: useRef(null),
    contentType: useRef(null),
    caption: useRef(null),
    publishing: useRef(null),
  };

  // ============================================================
  // CLEAR ORGANIZATION-SCOPED SELECTIONS
  // ============================================================

  useEffect(() => {
    setValue("social_account_ids", [], { shouldValidate: false });
    setValue("platforms", [], { shouldValidate: false });
    setValue("platform_content_types", {}, { shouldValidate: false });
  }, [selectedOrganizationId, setValue]);

  // ============================================================
  // CREATE POST
  // ============================================================

  async function handleCreatePost(data) {
    /*
     * React Hook Form + Zod have already
     * validated the form before this handler.
     */

    if (isSubmitting) {
      return;
    }

    try {
      setIsSubmitting(true);

      // ========================================================
      // BUILD PAYLOAD
      // ========================================================

      const payload = buildCreatePostPayload(data, socialAccounts);

      const response = await postService.createPost(data.organization, payload);

      if (!response?.success) {
        throw new Error(response?.message || "Unable to create the post.");
      }

      if (data.publish_type === "NOW") {
        toast.success(response.message || "Post created successfully.");
      }

      if (data.publish_type === "SCHEDULE") {
        toast.success(response.message || "Post scheduled successfully.");
      }

      if (data.publish_type === "DRAFT") {
        toast.success(response.message || "Draft saved successfully.");
      }
    } catch (error) {
      console.error("Create post failed:", error);

      const message =
        error?.response?.data?.message ||
        error?.message ||
        "Unable to create the post.";

      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  // ============================================================
  // VALIDATION ERROR
  // ============================================================

  function handleValidationError(validationErrors) {
    console.error("Create Post Validation Errors:", validationErrors);

    toast.error("Please fix the highlighted fields before publishing.");

    // ----------------------------------------------------------
    // VALIDATION PRIORITY
    // ----------------------------------------------------------

    const errorOrder = [
      {
        key: "organization",
        ref: sectionRefs.organization,
      },

      {
        key: "media",
        ref: sectionRefs.media,
      },

      {
        key: "platforms",
        ref: sectionRefs.platforms,
      },

      {
        key: "social_account_ids",
        ref: sectionRefs.platforms,
      },

      {
        key: "platform_content_types",
        ref: sectionRefs.contentType,
      },

      {
        key: "caption",
        ref: sectionRefs.caption,
      },

      {
        key: "publish_date",
        ref: sectionRefs.publishing,
      },

      {
        key: "publish_time",
        ref: sectionRefs.publishing,
      },

      {
        key: "timezone",
        ref: sectionRefs.publishing,
      },
    ];

    const firstInvalidSection = errorOrder.find(({ key }) =>
      Boolean(validationErrors?.[key]),
    );

    if (!firstInvalidSection) {
      return;
    }

    // ----------------------------------------------------------
    // SCROLL TO FIRST INVALID SECTION
    // ----------------------------------------------------------

    window.setTimeout(() => {
      firstInvalidSection.ref.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }, 50);
  }

  // ============================================================
  // LOADING
  // ============================================================

  if (isLoadingOrganizations) {
    return null;
  }

  // ============================================================
  // LOAD ERROR
  // ============================================================

  if (organizationsError || !organizationsResponse?.success) {
    return (
      <Box
        sx={{
          p: 4,
          color: "error.main",
        }}
      >
        {organizationsError?.message || "Unable to load Create Post."}
      </Box>
    );
  }

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <FormProvider {...methods}>
      <Box
        component="form"
        noValidate
        onSubmit={handleSubmit(handleCreatePost, handleValidationError)}
      >
        <Grid container spacing={4} alignItems="flex-start">
          {/* ==================================================
              LEFT
          ================================================== */}

          <Grid
            size={{
              xs: 12,
              lg: 8,
            }}
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                gap: 4,
              }}
            >
              {/* ==============================================
                  ORGANIZATION
              ============================================== */}

              <Box ref={sectionRefs.organization}>
                <OrganizationSection
                  organizations={organizations}
                />
              </Box>

              {/* ==============================================
                  MEDIA
              ============================================== */}

              <Box ref={sectionRefs.media}>
                <MediaUploadSection config={createPostData.media} />
              </Box>

              {/* ==============================================
                  PUBLISHING ACCOUNTS
              ============================================== */}

              <Box ref={sectionRefs.platforms}>
                <PlatformSection
                  platforms={createPostData.platforms}
                  accounts={socialAccounts}
                />
              </Box>

              {/* ==============================================
                  CONTENT TYPE
              ============================================== */}

              <Box ref={sectionRefs.contentType}>
                <ContentTypeSection platforms={createPostData.platforms} />
              </Box>

              {/* ==============================================
                  AI CAPTION
              ============================================== */}

              <AICaptionSection />

              {/* ==============================================
                  CAPTION
              ============================================== */}

              <Box ref={sectionRefs.caption}>
                <CaptionSection />
              </Box>
            </Box>
          </Grid>

          {/* ==================================================
              RIGHT
          ================================================== */}

          <Grid
            size={{
              xs: 12,
              lg: 4,
            }}
          >
            <Box
              sx={{
                position: {
                  lg: "sticky",
                },

                top: 24,

                display: "flex",

                flexDirection: "column",

                gap: 3,
              }}
            >
              {/* ==============================================
                  LIVE PREVIEW
              ============================================== */}

              <LivePreviewSection
                organizations={organizations}
                platforms={createPostData.platforms}
                accounts={socialAccounts}
              />

              {/* ==============================================
                  PUBLISHING
              ============================================== */}

              <Box ref={sectionRefs.publishing}>
                <PublishingSection loading={isSubmitting || formIsSubmitting} />
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </FormProvider>
  );
}
