import { z } from "zod";

import { PLATFORM_IDS } from "../constants/platforms/platformCapabilities";

import { getPlatformStates } from "../utils/post/platformCapability.utils";

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
// CREATE POST SCHEMA
// ============================================================

export const createPostSchema = z
  .object({
    // ==========================================================
    // ORGANIZATION
    // ==========================================================

    organization: z.string().trim().min(1, "Organization is required"),

    // ==========================================================
    // PLATFORMS
    // ==========================================================
    //
    // Platform selection is derived from selected social
    // accounts.
    //
    // `social_account_ids` is the actual user selection.
    //
    // ==========================================================

    platforms: z.array(z.string().trim().min(1)),

    // ==========================================================
    // SOCIAL ACCOUNTS
    // ==========================================================
    //
    // Exact connected accounts selected for publishing.
    //
    // Multiple accounts from the same platform are allowed.
    //
    // ==========================================================

    social_account_ids: z
      .array(z.string().trim().min(1))
      .min(1, "Select at least one social account."),

    // ==========================================================
    // PLATFORM CONTENT TYPES
    // ==========================================================

    platform_content_types: z.record(z.string(), z.string()),

    // ==========================================================
    // MEDIA
    // ==========================================================

    media: z.array(z.any()).min(1, "Upload at least one media file"),

    // ==========================================================
    // CAPTION
    // ==========================================================

    caption: z
      .string()
      .trim()
      .min(1, "Caption is required")
      .max(2200, "Caption cannot exceed 2200 characters"),

    // ==========================================================
    // AI
    // ==========================================================

    ai_prompt: z.string().optional(),

    ai_tone: z.string().min(1, "AI tone is required"),

    ai_length: z.string().min(1, "AI caption length is required"),

    ai_include_emoji: z.boolean(),

    ai_include_hashtags: z.boolean(),

    ai_include_cta: z.boolean(),

    // ==========================================================
    // PUBLISHING
    // ==========================================================

    publish_type: z.enum(["NOW", "SCHEDULE", "DRAFT"]),

    publish_date: z.string().optional(),

    publish_time: z.string().optional(),

    timezone: z.string().min(1, "Timezone is required"),
  })

  // ============================================================
  // CROSS-FIELD VALIDATION
  // ============================================================

  .superRefine((data, ctx) => {
    // ========================================================
    // BASIC REFERENCES
    // ========================================================

    const selectedPlatforms = data.platforms || [];

    const selectedAccountIds = data.social_account_ids || [];

    const selectedContentTypes = data.platform_content_types || {};

    const media = data.media || [];

    // ========================================================
    // DUPLICATE SOCIAL ACCOUNTS
    // ========================================================

    const uniqueAccountIds = new Set(selectedAccountIds);

    if (uniqueAccountIds.size !== selectedAccountIds.length) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,

        path: ["social_account_ids"],

        message: "Duplicate social accounts are not allowed.",
      });
    }

    // ========================================================
    // UNSUPPORTED PLATFORMS
    // ========================================================
    //
    // Platforms are derived internally from selected accounts.
    // This validation protects the payload from unexpected
    // unsupported platform values.
    //
    // ========================================================

    selectedPlatforms.forEach((platformId, index) => {
      if (!SUPPORTED_PLATFORM_IDS.has(platformId)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,

          path: ["platforms", index],

          message: "This platform is not supported.",
        });
      }
    });

    // ========================================================
    // MEDIA
    // ========================================================
    //
    // The field-level `.min(1)` validation already handles
    // missing media.
    //
    // ========================================================

    // ========================================================
    // CAPABILITY STATES
    // ========================================================

    const platformStates = getPlatformStates({
      media,
    });

    const capabilityMap = new Map(
      platformStates.map((state) => [state.platform, state]),
    );

    // ========================================================
    // CONTENT TYPE VALIDATION
    // ========================================================
    //
    // Every selected platform must have a valid content type.
    //
    // ========================================================

    selectedPlatforms.forEach((platformId) => {
      const platformState = capabilityMap.get(platformId);

      // ----------------------------------------------------
      // PLATFORM NOT SUPPORTED BY CURRENT MEDIA
      // ----------------------------------------------------
      //
      // The account-selection UI prevents these accounts from
      // being selected.
      //
      // Don't create another platform error here.
      //
      // ----------------------------------------------------

      if (!platformState?.available) {
        return;
      }

      // ----------------------------------------------------
      // CONTENT TYPE REQUIRED
      // ----------------------------------------------------

      const contentType = selectedContentTypes[platformId];

      if (!contentType) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,

          path: ["platform_content_types", platformId],

          message: `Select a content type for ${formatPlatformName(
            platformId,
          )}.`,
        });

        return;
      }

      // ----------------------------------------------------
      // CONTENT TYPE EXISTS
      // ----------------------------------------------------

      const contentTypeState = platformState.contentTypes?.find(
        (item) => item.value === contentType,
      );

      if (!contentTypeState) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,

          path: ["platform_content_types", platformId],

          message:
            "The selected content type is not supported on this platform.",
        });

        return;
      }

      // ----------------------------------------------------
      // CONTENT TYPE COMPATIBILITY
      // ----------------------------------------------------

      if (!contentTypeState.available) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,

          path: ["platform_content_types", platformId],

          message:
            contentTypeState.reason ||
            "The selected content type is not compatible with the current media.",
        });
      }
    });

    // ========================================================
    // STALE CONTENT TYPE ENTRIES
    // ========================================================
    //
    // Example:
    //
    // platforms:
    //   ["INSTAGRAM"]
    //
    // platform_content_types:
    //   {
    //     INSTAGRAM: "POST",
    //     FACEBOOK: "POST"
    //   }
    //
    // Facebook is no longer selected.
    //
    // ========================================================

    Object.keys(selectedContentTypes).forEach((platformId) => {
      if (!selectedPlatforms.includes(platformId)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,

          path: ["platform_content_types", platformId],

          message:
            "Content type configuration exists for an unselected platform.",
        });
      }
    });

    // ========================================================
    // PUBLISHING VALIDATION
    // ========================================================

    if (data.publish_type === "SCHEDULE") {
      // ------------------------------------------------------
      // DATE
      // ------------------------------------------------------

      if (!data.publish_date) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,

          path: ["publish_date"],

          message: "Publish date is required.",
        });
      }

      // ------------------------------------------------------
      // TIME
      // ------------------------------------------------------

      if (!data.publish_time) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,

          path: ["publish_time"],

          message: "Publish time is required.",
        });
      }

      // ------------------------------------------------------
      // TIMEZONE
      // ------------------------------------------------------

      if (!data.timezone) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,

          path: ["timezone"],

          message: "Timezone is required.",
        });
      }
    }
  });

// ============================================================
// PLATFORM NAME HELPER
// ============================================================

function formatPlatformName(platformId) {
  const names = {
    [PLATFORM_IDS.INSTAGRAM]: "Instagram",

    [PLATFORM_IDS.FACEBOOK]: "Facebook",

    [PLATFORM_IDS.LINKEDIN]: "LinkedIn",

    [PLATFORM_IDS.YOUTUBE]: "YouTube",
  };

  return names[platformId] || platformId;
}
