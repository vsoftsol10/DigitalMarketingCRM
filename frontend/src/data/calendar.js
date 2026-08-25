// ==========================================
// CALENDAR MOCK DATA
// ==========================================
//
// Temporary frontend data for calendar UI development.
//
// IMPORTANT:
// UI components should NOT import this file directly.
//
// Data flow:
//
// calendar.js
//     ↓
// calendar.service.js
//     ↓
// calendar.api.js
//     ↓
// Django Calendar API
//
// Later backend integration:
// calendar.service.js will switch from mock data
// to API data without changing calendar UI components.
//
// ==========================================

export const CALENDAR_EVENTS = [
  // ==========================================
  // EVENT 001
  // ==========================================

  {
    id: "CAL001",

    title: "Summer Product Launch",

    date: "2026-08-03",
    time: "09:00 AM",

    organization: {
      id: "ORG001",
      name: "Lumen Coffee Co.",
    },

    platform: "INSTAGRAM",

    contentType: "REEL",

    status: "PUBLISHED",

    caption:
      "Introducing our latest summer collection. Discover your new favorite coffee experience.",

    media: [
      {
        id: "MEDIA001",
        type: "IMAGE",
        url: "/images/calendar/demo-coffee.jpg",
      },
    ],

    color: "#E11D48",
    backgroundColor: "#FFF1F2",

    timezone: "Asia/Kolkata",

    createdAt: "2026-08-01T10:00:00+05:30",
    updatedAt: "2026-08-03T09:00:00+05:30",
  },

  // ==========================================
  // EVENT 002
  // ==========================================

  {
    id: "CAL002",

    title: "Fitness Transformation Tips",

    date: "2026-08-05",
    time: "11:00 AM",

    organization: {
      id: "ORG002",
      name: "Atlas Fitness",
    },

    platform: "FACEBOOK",

    contentType: "POST",

    status: "PUBLISHED",

    caption:
      "Small consistent habits create big transformations. Start your fitness journey today.",

    media: [],

    color: "#2563EB",
    backgroundColor: "#EFF6FF",

    timezone: "Asia/Kolkata",

    createdAt: "2026-08-02T09:00:00+05:30",
    updatedAt: "2026-08-05T11:00:00+05:30",
  },

  // ==========================================
  // EVENT 003
  // ==========================================

  {
    id: "CAL003",

    title: "Outdoor Adventure Guide",

    date: "2026-08-07",
    time: "02:00 PM",

    organization: {
      id: "ORG003",
      name: "NorthPeak Outdoors",
    },

    platform: "LINKEDIN",

    contentType: "CAROUSEL",

    status: "SCHEDULED",

    caption:
      "Everything you need to know before planning your next outdoor adventure.",

    media: [],

    color: "#7C3AED",
    backgroundColor: "#F5F3FF",

    timezone: "Asia/Kolkata",

    createdAt: "2026-08-04T12:00:00+05:30",
    updatedAt: "2026-08-04T12:00:00+05:30",
  },

  // ==========================================
  // EVENT 004
  // ==========================================

  {
    id: "CAL004",

    title: "Weekend Special Offer",

    date: "2026-08-09",
    time: "06:00 PM",

    organization: {
      id: "ORG001",
      name: "Lumen Coffee Co.",
    },

    platform: "INSTAGRAM",

    contentType: "STORY",

    status: "SCHEDULED",

    caption:
      "Weekend is here. Enjoy our special offer and make your evening better.",

    media: [],

    color: "#F59E0B",
    backgroundColor: "#FFFBEB",

    timezone: "Asia/Kolkata",

    createdAt: "2026-08-06T10:00:00+05:30",
    updatedAt: "2026-08-06T10:00:00+05:30",
  },

  // ==========================================
  // EVENT 005
  // ==========================================

  {
    id: "CAL005",

    title: "New Training Program",

    date: "2026-08-11",
    time: "10:30 AM",

    organization: {
      id: "ORG002",
      name: "Atlas Fitness",
    },

    platform: "INSTAGRAM",

    contentType: "REEL",

    status: "SCHEDULED",

    caption:
      "Our new training program is designed to help you become stronger and healthier.",

    media: [],

    color: "#10B981",
    backgroundColor: "#ECFDF5",

    timezone: "Asia/Kolkata",

    createdAt: "2026-08-08T10:00:00+05:30",
    updatedAt: "2026-08-08T10:00:00+05:30",
  },

  // ==========================================
  // SAME DATE EVENT
  // EVENT 006
  // ==========================================

  {
    id: "CAL006",

    title: "Morning Product Tips",

    date: "2026-08-11",
    time: "09:00 AM",

    organization: {
      id: "ORG001",
      name: "Lumen Coffee Co.",
    },

    platform: "INSTAGRAM",

    contentType: "POST",

    status: "SCHEDULED",

    caption:
      "Start your morning with our latest product tips and recommendations.",

    media: [],

    color: "#E11D48",
    backgroundColor: "#FFF1F2",

    timezone: "Asia/Kolkata",

    createdAt: "2026-08-10T10:00:00+05:30",
    updatedAt: "2026-08-10T10:00:00+05:30",
  },

  // ==========================================
  // SAME DATE EVENT
  // EVENT 007
  // ==========================================

  {
    id: "CAL007",

    title: "Fitness Motivation",

    date: "2026-08-11",
    time: "01:00 PM",

    organization: {
      id: "ORG002",
      name: "Atlas Fitness",
    },

    platform: "FACEBOOK",

    contentType: "POST",

    status: "SCHEDULED",

    caption:
      "Stay consistent, stay focused, and keep moving towards your fitness goals.",

    media: [],

    color: "#2563EB",
    backgroundColor: "#EFF6FF",

    timezone: "Asia/Kolkata",

    createdAt: "2026-08-10T11:00:00+05:30",
    updatedAt: "2026-08-10T11:00:00+05:30",
  },

  // ==========================================
  // SAME DATE EVENT
  // EVENT 008
  // ==========================================

  {
    id: "CAL008",

    title: "Evening Special Offer",

    date: "2026-08-11",
    time: "06:00 PM",

    organization: {
      id: "ORG001",
      name: "Lumen Coffee Co.",
    },

    platform: "INSTAGRAM",

    contentType: "STORY",

    status: "SCHEDULED",

    caption:
      "Enjoy our special evening offer and make your day a little better.",

    media: [],

    color: "#F59E0B",
    backgroundColor: "#FFFBEB",

    timezone: "Asia/Kolkata",

    createdAt: "2026-08-10T12:00:00+05:30",
    updatedAt: "2026-08-10T12:00:00+05:30",
  },

  // ==========================================
  // EVENT 009
  // ==========================================

  {
    id: "CAL009",

    title: "Coffee Brewing Tips",

    date: "2026-08-14",
    time: "08:30 AM",

    organization: {
      id: "ORG001",
      name: "Lumen Coffee Co.",
    },

    platform: "FACEBOOK",

    contentType: "VIDEO",

    status: "SCHEDULED",

    caption:
      "Learn simple techniques to improve your coffee brewing experience at home.",

    media: [],

    color: "#2563EB",
    backgroundColor: "#EFF6FF",

    timezone: "Asia/Kolkata",

    createdAt: "2026-08-09T09:00:00+05:30",
    updatedAt: "2026-08-09T09:00:00+05:30",
  },

  // ==========================================
  // EVENT 010
  // ==========================================

  {
    id: "CAL010",

    title: "Customer Success Story",

    date: "2026-08-18",
    time: "04:00 PM",

    organization: {
      id: "ORG002",
      name: "Atlas Fitness",
    },

    platform: "LINKEDIN",

    contentType: "POST",

    status: "DRAFT",

    caption:
      "A real customer story showing the impact of consistent training and commitment.",

    media: [],

    color: "#64748B",
    backgroundColor: "#F8FAFC",

    timezone: "Asia/Kolkata",

    createdAt: "2026-08-10T11:00:00+05:30",
    updatedAt: "2026-08-10T11:00:00+05:30",
  },

  // ==========================================
  // EVENT 011
  // ==========================================

  {
    id: "CAL011",

    title: "Adventure Essentials",

    date: "2026-08-20",
    time: "12:00 PM",

    organization: {
      id: "ORG003",
      name: "NorthPeak Outdoors",
    },

    platform: "YOUTUBE",

    contentType: "VIDEO",

    status: "SCHEDULED",

    caption:
      "The essential gear checklist for your next outdoor adventure.",

    media: [],

    color: "#F97316",
    backgroundColor: "#FFF7ED",

    timezone: "Asia/Kolkata",

    createdAt: "2026-08-10T12:00:00+05:30",
    updatedAt: "2026-08-10T12:00:00+05:30",
  },

  // ==========================================
  // EVENT 012
  // ==========================================

  {
    id: "CAL012",

    title: "Monthly Community Update",

    date: "2026-08-24",
    time: "05:30 PM",

    organization: {
      id: "ORG001",
      name: "Lumen Coffee Co.",
    },

    platform: "THREADS",

    contentType: "POST",

    status: "SCHEDULED",

    caption:
      "Here is what is happening in our community this month.",

    media: [],

    color: "#8B5CF6",
    backgroundColor: "#F5F3FF",

    timezone: "Asia/Kolkata",

    createdAt: "2026-08-10T13:00:00+05:30",
    updatedAt: "2026-08-10T13:00:00+05:30",
  },

  // ==========================================
  // EVENT 013
  // ==========================================

  {
    id: "CAL013",

    title: "Monthly Campaign Recap",

    date: "2026-08-28",
    time: "07:00 PM",

    organization: {
      id: "ORG003",
      name: "NorthPeak Outdoors",
    },

    platform: "X",

    contentType: "POST",

    status: "PUBLISHED",

    caption:
      "A quick recap of this month's campaign and community highlights.",

    media: [],

    color: "#0F172A",
    backgroundColor: "#F8FAFC",

    timezone: "Asia/Kolkata",

    createdAt: "2026-08-05T15:00:00+05:30",
    updatedAt: "2026-08-28T19:00:00+05:30",
  },
];

// ==========================================
// CALENDAR FILTER OPTIONS
// ==========================================
//
// These are temporary UI options.
// Later these can come from:
// GET /calendar/filters/
//
// The component structure does not need to change.
// ==========================================

export const CALENDAR_FILTER_OPTIONS = {
  organizations: [
    {
      value: "ORG001",
      label: "Lumen Coffee Co.",
    },
    {
      value: "ORG002",
      label: "Atlas Fitness",
    },
    {
      value: "ORG003",
      label: "NorthPeak Outdoors",
    },
  ],

  platforms: [
    {
      value: "INSTAGRAM",
      label: "Instagram",
    },
    {
      value: "FACEBOOK",
      label: "Facebook",
    },
    {
      value: "LINKEDIN",
      label: "LinkedIn",
    },
    {
      value: "YOUTUBE",
      label: "YouTube",
    },
    {
      value: "THREADS",
      label: "Threads",
    },
    {
      value: "X",
      label: "X",
    },
  ],

  contentTypes: [
    {
      value: "POST",
      label: "Post",
    },
    {
      value: "REEL",
      label: "Reel",
    },
    {
      value: "STORY",
      label: "Story",
    },
    {
      value: "CAROUSEL",
      label: "Carousel",
    },
    {
      value: "VIDEO",
      label: "Video",
    },
    {
      value: "SHORT",
      label: "Short",
    },
  ],

  statuses: [
    {
      value: "DRAFT",
      label: "Draft",
    },
    {
      value: "SCHEDULED",
      label: "Scheduled",
    },
    {
      value: "PUBLISHED",
      label: "Published",
    },
    {
      value: "FAILED",
      label: "Failed",
    },
  ],
};