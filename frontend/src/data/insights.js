export const INSIGHTS = {
  filters: {
    organization: "all",
    period: "30D",
  },

  statistics: {
    total_reach: 2700000,
    total_reach_change: 12.4,

    engagement: 18100,
    engagement_change: 5.1,

    engagement_rate: 4.9,
    engagement_rate_change: -0.3,

    followers: 341600,
    followers_change: 3.2,
  },

  reach_chart: [
    { label: "Jul 1", reach: 120000 },
    { label: "Jul 5", reach: 180000 },
    { label: "Jul 10", reach: 260000 },
    { label: "Jul 15", reach: 420000 },
    { label: "Jul 20", reach: 610000 },
    { label: "Jul 25", reach: 820000 },
    { label: "Jul 30", reach: 1050000 },
  ],

  platform_mix: [
    {
      platform: "Instagram",
      value: 42,
      color: "#2563EB",
    },
    {
      platform: "Facebook",
      value: 28,
      color: "#10B981",
    },
    {
      platform: "LinkedIn",
      value: 18,
      color: "#8B5CF6",
    },
    {
      platform: "YouTube",
      value: 12,
      color: "#F97316",
    },
  ],

  best_time: [
    { day: "Mon", hour: "9 AM", score: 95 },
    { day: "Tue", hour: "11 AM", score: 88 },
    { day: "Wed", hour: "2 PM", score: 92 },
    { day: "Thu", hour: "10 AM", score: 98 },
    { day: "Fri", hour: "1 PM", score: 85 },
    { day: "Sat", hour: "12 PM", score: 70 },
    { day: "Sun", hour: "6 PM", score: 80 },
  ],

  engagement_types: [
    {
      id: "likes",
      label: "Likes",
      value: 95,
      color: "#EF4444",
    },
    {
      id: "comments",
      label: "Comments",
      value: 24,
      color: "#2563EB",
    },
    {
      id: "shares",
      label: "Shares",
      value: 15,
      color: "#10B981",
    },
    {
      id: "saves",
      label: "Saves",
      value: 32,
      color: "#F97316",
    },
    {
      id: "dms",
      label: "DMs",
      value: 10,
      color: "#8B5CF6",
    },
  ],

  accounts: [
  {
    id: "ACC001",

    account_name: "Lumen Coffee",

    organization: "Lumen Coffee Co.",

    avatar: "LC",

    avatar_color: "#2563EB",

    platform: "INSTAGRAM",

    followers: 32400,

    engagement_rate: 4.8,

    reach: 259200,

    trend: [18, 22, 20, 28, 26, 32, 36],
  },

  {
    id: "ACC002",

    account_name: "Atlas Fitness",

    organization: "Atlas Fitness",

    avatar: "AF",

    avatar_color: "#10B981",

    platform: "FACEBOOK",

    followers: 12800,

    engagement_rate: 2.9,

    reach: 102400,

    trend: [8, 10, 9, 12, 13, 15, 17],
  },

  {
    id: "ACC003",

    account_name: "NorthPeak",

    organization: "NorthPeak Outdoors",

    avatar: "NP",

    avatar_color: "#F97316",

    platform: "YOUTUBE",

    followers: 64000,

    engagement_rate: 5.2,

    reach: 418500,

    trend: [20, 24, 22, 26, 31, 35, 38],
  },
], 
};
