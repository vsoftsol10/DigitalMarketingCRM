import { FormProvider, useForm } from "react-hook-form";

import { zodResolver } from "@hookform/resolvers/zod";

import toast from "react-hot-toast";

import { Box, Grid } from "@mui/material";

import { useEffect, useRef, useState } from "react";

import postService from "../../services/post.service";

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

import { SOCIAL_ACCOUNT_DUMMY_DATA } from "../../constants/social/socialAccountDummyData";

export default function CreatePost() {
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

    formState: { isSubmitting: formIsSubmitting, errors },
  } = methods;

  // ============================================================
  // PAGE DATA
  // ============================================================

  const [createPostData, setCreatePostData] = useState(null);

  const [isLoadingData, setIsLoadingData] = useState(true);

  const [loadDataError, setLoadDataError] = useState(null);

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
  // LOAD CREATE POST DATA
  // ============================================================

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      try {
        setIsLoadingData(true);
        setLoadDataError(null);

        const response = await postService.getCreatePostData();

        if (!isMounted) {
          return;
        }

        setCreatePostData(response);
      } catch (error) {
        console.error("Failed to load create post data:", error);

        if (!isMounted) {
          return;
        }

        setLoadDataError("Unable to load the Create Post page.");
      } finally {
        if (isMounted) {
          setIsLoadingData(false);
        }
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, []);

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

      const payload = buildCreatePostPayload(data);

      console.log("Create Post Payload:", payload);

      /*
       * Backend create-post API is not connected yet.
       *
       * Later:
       *
       * const response =
       *   await postService.createPost(payload);
       */

      // ========================================================
      // TEMPORARY DEVELOPMENT FEEDBACK
      // ========================================================

      if (data.publish_type === "NOW") {
        toast.success("Post data is ready to publish.");
      }

      if (data.publish_type === "SCHEDULE") {
        toast.success("Post scheduling data is ready.");
      }

      if (data.publish_type === "DRAFT") {
        toast.success("Draft data is ready to save.");
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

  if (isLoadingData) {
    return null;
  }

  // ============================================================
  // LOAD ERROR
  // ============================================================

  if (loadDataError || !createPostData) {
    return (
      <Box
        sx={{
          p: 4,
          color: "error.main",
        }}
      >
        {loadDataError || "Unable to load Create Post."}
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
                  organizations={createPostData.organizations}
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
                  accounts={SOCIAL_ACCOUNT_DUMMY_DATA}
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
                organizations={createPostData.organizations}
                platforms={createPostData.platforms}
                accounts={SOCIAL_ACCOUNT_DUMMY_DATA}
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
