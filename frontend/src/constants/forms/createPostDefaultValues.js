export const createPostDefaultValues = {
  // ============================================================
  // ORGANIZATION
  // ============================================================

  organization: "",

  // ============================================================
  // SOCIAL PLATFORMS
  // ============================================================

  platforms: [],

  // ============================================================
  // CONNECTED SOCIAL ACCOUNTS
  // ============================================================
  //
  // Stores the exact connected social account IDs selected
  // for publishing.
  //
  // Example:
  //
  // [
  //   "instagram-account-001",
  //   "instagram-account-003",
  //   "facebook-page-002",
  // ]
  //
  // Platform selection and account selection are intentionally
  // kept separate.
  // ============================================================

  social_account_ids: [],

  // ============================================================
  // PLATFORM CONTENT TYPES
  // ============================================================

  platform_content_types: {},

  // ============================================================
  // MEDIA
  // ============================================================

  media: [],

  // ============================================================
  // CAPTION
  // ============================================================

  caption: "",

  // ============================================================
  // AI
  // ============================================================

  ai_prompt: "",

  ai_tone: "PROFESSIONAL",

  ai_length: "MEDIUM",

  ai_include_emoji: true,

  ai_include_hashtags: true,

  ai_include_cta: true,

  // ============================================================
  // PUBLISHING
  // ============================================================

  publish_type: "NOW",

  publish_date: "",

  publish_time: "",

  timezone: "Asia/Kolkata",
};
