// import { z } from "zod";

// export const contentIdeaSchema = z.object({
//   organization: z.string().min(1, "Organization is required"),

//   title: z
//     .string()
//     .trim()
//     .min(3, "Title must be at least 3 characters")
//     .max(120, "Title cannot exceed 120 characters"),

//   platform: z.string().min(1, "Platform is required"),

//   content_type: z.string().min(1, "Content type is required"),

//   target_publish_date: z.string().min(1, "Target publish date is required"),

//   campaign_goal: z.string().min(1, "Campaign goal is required"),

//   description: z
//     .string()
//     .max(1000, "Description cannot exceed 1000 characters")
//     .optional(),
// });
import { z } from "zod";

const CONTENT_TYPES_BY_PLATFORM = {
  INSTAGRAM: ["POST", "REEL", "STORY", "CAROUSEL"],

  FACEBOOK: ["POST", "REEL", "STORY", "CAROUSEL", "VIDEO"],

  YOUTUBE: ["SHORT", "VIDEO"],

  LINKEDIN: ["POST", "CAROUSEL", "VIDEO"],

  X: ["POST", "VIDEO"],
};

export const contentIdeaSchema = z
  .object({
    organization: z.string().min(1, "Organization is required"),

    title: z
      .string()
      .trim()
      .min(3, "Title must be at least 3 characters")
      .max(120, "Title cannot exceed 120 characters"),

    platform: z.string().min(1, "Platform is required"),

    content_type: z.string().min(1, "Content type is required"),

    target_publish_date: z.string().min(1, "Target publish date is required"),

    campaign_goal: z.string().min(1, "Campaign goal is required"),

    description: z
      .string()
      .max(1000, "Description cannot exceed 1000 characters")
      .optional(),
  })
  .superRefine((data, context) => {
    const allowedTypes = CONTENT_TYPES_BY_PLATFORM[data.platform];

    if (!allowedTypes) {
      return;
    }

    if (!allowedTypes.includes(data.content_type)) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["content_type"],
        message:
          "Selected content type is not supported by the selected platform.",
      });
    }
  });
