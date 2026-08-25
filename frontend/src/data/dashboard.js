export const DASHBOARD = {
  statistics: {
    total_organizations: 5,
    connected_social_accounts: 9,
    scheduled_posts_today: 0,
    active_campaigns: 4,
  },

  today_schedule: {
    total_posts: 0,
    items: [],
  },

  notifications: [
    {
      id: "NOT001",
      type: "FAILED_POST",
      title: "Failed Post",
      message:
        "Gear Review: Rain Shells — YouTube API quota exceeded — retry after midnight.",
      organization: "NorthPeak Outdoors",
      created_at: "2026-08-04T09:30:00Z",
    },

    {
      id: "NOT002",
      type: "TOKEN_EXPIRING",
      title: "Token Expiring Soon",
      message: "YouTube connection expires soon.",
      organization: "Atlas Fitness",
      created_at: "2026-08-04T08:30:00Z",
    },

    {
      id: "NOT003",
      type: "PENDING_ACTION",
      title: "Pending Action",
      message: 'Content idea "Customer Quote Spotlight" is ready to create.',
      organization: "Lumen Coffee Co.",
      created_at: "2026-08-04T08:00:00Z",
    },
  ],

  recent_activities: [
    {
      id: "ACT001",
      type: "POST_PUBLISHED",
      title: "Post Published — Roastery Tour",
      subtitle: "Instagram • Lumen Coffee Co.",
      created_at: "2026-07-26T12:00:00Z",
    },

    {
      id: "ACT002",
      type: "POST_PUBLISHED",
      title: "Post Published — Member Spotlight",
      subtitle: "Instagram • Atlas Fitness",
      created_at: "2026-07-28T09:00:00Z",
    },

    {
      id: "ACT003",
      type: "ORGANIZATION_CREATED",
      title: "Organization Created — Lumen Coffee Co.",
      subtitle: "Food & Beverage",
      created_at: "2025-02-12T09:00:00Z",
    },
  ],

  quick_actions: [
    {
      id: "QA001",
      title: "Create Post",
      path: "/posts/new",
      icon: "post",
    },

    {
      id: "QA002",
      title: "Open Content Planner",
      path: "/planner",
      icon: "planner",
    },

    {
      id: "QA003",
      title: "Create Organization",
      path: "/organizations/new",
      icon: "organization",
    },
  ],
};
