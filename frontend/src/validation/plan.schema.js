// import { z } from "zod";

// export const planSchema = z.object({
//   name: z
//     .string()
//     .trim()
//     .min(1, "Plan name is required")
//     .max(100, "Plan name must be 100 characters or less"),

//   description: z
//     .string()
//     .trim()
//     .min(1, "Plan description is required")
//     .max(500, "Plan description must be 500 characters or less"),

//   type: z.enum(["Basic", "Professional", "Premium", "Advanced", "Custom"]),

//   status: z.enum(["active", "inactive"]),

//   billing_cycle: z.enum(["monthly", "yearly"]),

//   monthly_price: z.coerce.number().min(0, "Monthly price cannot be negative"),

//   yearly_price: z.coerce.number().min(0, "Yearly price cannot be negative"),

//   limits: z.object({
//     accounts: z.coerce.number().int().min(0),

//     posts: z.coerce.number().int().min(0),

//     videos: z.coerce.number().int().min(0),

//     ads: z.coerce.number().int().min(0),

//     storage_gb: z.coerce.number().min(0),

//     dm_automations: z.coerce.number().int().min(0),
//   }),

//   highlights: z
//     .string()
//     .trim()
//     .max(1000, "Highlights must be 1000 characters or less")
//     .optional(),
// });
import { z } from "zod";

export const planSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Plan name is required")
    .max(
      100,
      "Plan name must be 100 characters or less",
    ),

  type: z
    .string()
    .trim()
    .min(1, "Plan type is required")
    .max(
      100,
      "Plan type is required",
    ),

  description: z
    .string()
    .trim()
    .min(1, "Plan description is required")
    .max(
      500,
      "Plan description must be 500 characters or less",
    ),

  status: z.enum([
    "active",
    "inactive",
  ]),

  monthly_price: z.coerce
    .number()
    .min(
      0,
      "Monthly price cannot be negative",
    ),

  yearly_price: z.coerce
    .number()
    .min(
      0,
      "Yearly price cannot be negative",
    ),

  limits: z.object({
    accounts: z.coerce
      .number()
      .int()
      .min(0),

    posts: z.coerce
      .number()
      .int()
      .min(0),

    videos: z.coerce
      .number()
      .int()
      .min(0),

    ads: z.coerce
      .number()
      .int()
      .min(0),

    dm_automations: z.coerce
      .number()
      .int()
      .min(0),
  }),

  highlights: z
    .string()
    .trim()
    .max(
      1000,
      "Highlights must be 1000 characters or less",
    )
    .optional(),
});