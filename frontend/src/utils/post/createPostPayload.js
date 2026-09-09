export function buildCreatePostPayload(data) {
  const media = Array.isArray(data.media) ? data.media : [];

  const platforms = Array.isArray(data.platforms) ? data.platforms : [];

  const socialAccountIds = Array.isArray(data.social_account_ids)
    ? data.social_account_ids.filter(Boolean)
    : [];

  const platformContentTypes =
    data.platform_content_types &&
    typeof data.platform_content_types === "object"
      ? data.platform_content_types
      : {};

  return {
    // ==========================================================
    // ORGANIZATION
    // ==========================================================

    organization: data.organization,

    // ==========================================================
    // PLATFORMS
    // ==========================================================
    //
    // Selected platform IDs are still included because they are
    // required for platform-level capability and content-type
    // handling.
    //
    // ==========================================================

    platforms,

    // ==========================================================
    // SOCIAL ACCOUNTS
    // ==========================================================
    //
    // Exact connected social account IDs selected for publishing.
    //
    // Multiple accounts from the same platform are supported.
    //
    // Example:
    //
    // [
    //   "instagram-account-001",
    //   "instagram-account-002",
    //   "facebook-page-001",
    // ]
    //
    // Backend will later validate:
    //
    // - account belongs to organization
    // - account belongs to a selected platform
    // - account is connected
    // - account is valid / publishable
    //
    // ==========================================================

    social_account_ids: socialAccountIds,

    // ==========================================================
    // PLATFORM CONTENT TYPES
    // ==========================================================

    platform_content_types: Object.fromEntries(
      platforms
        .filter((platformId) => platformContentTypes[platformId])
        .map((platformId) => [platformId, platformContentTypes[platformId]]),
    ),

    // ==========================================================
    // MEDIA
    // ==========================================================

    media: media.map((item, index) => ({
      id: item.id,

      order: index,

      type: item.type,

      name: item.name,

      mime_type: item.mime_type,

      size: item.size,

      /*
       * Local File object is intentionally retained for the
       * current frontend workflow.
       *
       * Backend upload implementation can later replace this
       * with a media upload / media_id flow.
       */

      file: item.file,

      /*
       * Server-side fields are included when already available.
       */

      media_id: item.media_id || null,

      url: item.url || null,
    })),

    // ==========================================================
    // CAPTION
    // ==========================================================

    caption: data.caption,

    // ==========================================================
    // AI
    // ==========================================================

    ai: {
      prompt: data.ai_prompt || "",

      tone: data.ai_tone,

      length: data.ai_length,

      include_emoji: Boolean(data.ai_include_emoji),

      include_hashtags: Boolean(data.ai_include_hashtags),

      include_cta: Boolean(data.ai_include_cta),
    },

    // ==========================================================
    // PUBLISHING
    // ==========================================================

    publishing: {
      type: data.publish_type,

      date: data.publish_type === "SCHEDULE" ? data.publish_date || null : null,

      time: data.publish_type === "SCHEDULE" ? data.publish_time || null : null,

      timezone: data.publish_type === "SCHEDULE" ? data.timezone || null : null,
    },
  };
}
