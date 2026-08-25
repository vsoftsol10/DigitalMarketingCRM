export const CONTENT_PLANNER = {
  filters: {
    organization: "all",
  },

  statistics: {
    total_ideas: 48,
    organizations: 12,
    posts_created: 31,
    this_month: 9,
  },

  organizations: [
    {
      id: "ORG001",
      name: "Lumen Coffee Co.",
    },
    {
      id: "ORG002",
      name: "Atlas Fitness",
    },
    {
      id: "ORG003",
      name: "NorthPeak Outdoors",
    },
  ],

  ideas: [
    {
      id: "IDEA001",

      title: "Morning Coffee Routine",

      description:
        "Show how to prepare the perfect morning coffee in under 30 seconds.",

      organization_id: "ORG001",

      organization: "Lumen Coffee Co.",

      platform: "INSTAGRAM",

      type: "REEL",

      goal: "BRAND_AWARENESS",

      target_publish_date: "2026-08-15",

      created_at: "2026-08-01T10:00:00Z",

      updated_at: "2026-08-01T10:00:00Z",
    },

    {
      id: "IDEA002",

      title: "Summer Fitness Challenge",

      description:
        "Launch a weekly challenge encouraging members to share workouts.",

      organization_id: "ORG002",

      organization: "Atlas Fitness",

      platform: "FACEBOOK",

      type: "POST",

      goal: "LEAD_GENERATION",

      target_publish_date: "2026-08-18",

      created_at: "2026-08-02T09:00:00Z",

      updated_at: "2026-08-02T09:00:00Z",
    },

    {
      id: "IDEA003",

      title: "Weekend Hiking Tips",

      description:
        "Share useful hiking safety tips with beautiful mountain visuals.",

      organization_id: "ORG003",

      organization: "NorthPeak Outdoors",

      platform: "YOUTUBE",

      type: "SHORT",

      goal: "ENGAGEMENT",

      target_publish_date: "2026-08-20",

      created_at: "2026-08-03T09:00:00Z",

      updated_at: "2026-08-03T09:00:00Z",
    },
  ],
};
