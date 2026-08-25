import { z } from "zod";

export const organizationSchema = z.object({
  // =====================================
  // Basic Information
  // =====================================

  name: z
    .string()
    .trim()
    .min(1, "Organization name is required"),

  description: z
    .string()
    .optional(),

  industry: z
    .string()
    .min(1, "Industry is required"),

  website: z
    .string()
    .url("Enter a valid website URL")
    .or(z.literal("")),

  location: z
    .string()
    .optional(),

  organization_status: z
    .string()
    .default("ACTIVE"),

  logo_color: z
    .string()
    .optional(),

  // =====================================
  // Contact
  // =====================================

  contact_name: z
    .string()
    .trim()
    .min(1, "Contact name is required"),

  contact_email: z
    .string()
    .trim()
    .email("Enter a valid email"),

  contact_phone: z
    .string()
    .optional(),

  // =====================================
  // Subscription
  // =====================================

  subscription_plan: z
    .string()
    .min(
      1,
      "Subscription plan is required",
    ),

  billing_cycle: z.enum([
    "monthly",
    "yearly",
  ]),

  // =====================================
  // Social Accounts
  // =====================================

  social_accounts: z
    .array(z.any())
    .default([]),
});