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

export const contentIdeaSchema = z.object({
  organization: z.string().min(1, "Organization is required"),
  social_account_ids: z.array(z.string()).min(1, "Select at least one publish account"),
  caption: z.string().trim().min(1, "Caption is required").max(2200, "Caption cannot exceed 2200 characters"),
  content_type: z.enum(["POST", "REEL", "STORY"], { message: "Select a valid content type" }),
  target_publish_date: z.string().min(1, "Target publish date is required"),
  target_publish_time: z.string().min(1, "Target publish time is required"),
  description: z.string().max(1000, "Description cannot exceed 1000 characters").optional(),
});
