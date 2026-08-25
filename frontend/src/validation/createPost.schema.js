import { z } from "zod";

export const createPostSchema = z
  .object({
    organization: z
      .string()
      .min(1, "Organization is required"),

    platforms: z
      .array(z.string())
      .min(1, "Select at least one platform"),

    platform_content_types: z.record(
      z.string(),
      z.string()
    ),

    media: z
      .array(z.any())
      .min(1, "Upload at least one media file"),

    caption: z
      .string()
      .trim()
      .min(1, "Caption is required")
      .max(
        2200,
        "Caption cannot exceed 2200 characters"
      ),

    // ---------- AI ----------

    ai_prompt: z.string().optional(),

    ai_tone: z.string(),

    ai_length: z.string(),

    ai_include_emoji: z.boolean(),

    ai_include_hashtags: z.boolean(),

    ai_include_cta: z.boolean(),

    // ---------- Publishing ----------

    publish_type: z.enum([
      "NOW",
      "SCHEDULE",
      "DRAFT",
    ]),

    publish_date: z.string().optional(),

    publish_time: z.string().optional(),

    timezone: z.string(),
  })
  .superRefine((data, ctx) => {
    if (data.publish_type === "SCHEDULE") {
      if (!data.publish_date) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["publish_date"],
          message: "Publish date is required",
        });
      }

      if (!data.publish_time) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["publish_time"],
          message: "Publish time is required",
        });
      }

      if (!data.timezone) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["timezone"],
          message: "Timezone is required",
        });
      }
    }
  });