// export const SOCIAL_ACCOUNT_DUMMY_DATA = [
//   {
//     id: "dummy-instagram-001",
//     platform: "instagram",
//     pageName: "Digital Marketing",
//     username: "@digitalmarketing",
//     profileImage: "",
//     connected: true,
//     valid: true,
//     lastSync: "2026-08-26T09:30:00.000Z",
//   },

//   {
//     id: "dummy-instagram-002",
//     platform: "instagram",
//     pageName: "Fashion Brand",
//     username: "@fashionbrand",
//     profileImage: "",
//     connected: true,
//     valid: true,
//     lastSync: "2026-08-26T09:20:00.000Z",
//   },

//   {
//     id: "dummy-instagram-003",
//     platform: "instagram",
//     pageName: "Food Studio",
//     username: "@foodstudio",
//     profileImage: "",
//     connected: true,
//     valid: true,
//     lastSync: "2026-08-26T09:10:00.000Z",
//   },

//   {
//     id: "dummy-facebook-001",
//     platform: "facebook",
//     pageName: "Digital Marketing Platform",
//     username: "Digital Marketing Platform",
//     profileImage: "",
//     connected: true,
//     valid: true,
//     lastSync: "2026-08-26T09:15:00.000Z",
//   },

//   {
//     id: "dummy-facebook-002",
//     platform: "facebook",
//     pageName: "Fashion Brand",
//     username: "Fashion Brand",
//     profileImage: "",
//     connected: true,
//     valid: true,
//     lastSync: "2026-08-26T09:05:00.000Z",
//   },

//   {
//     id: "dummy-linkedin-001",
//     platform: "linkedin",
//     pageName: "Digital Marketing Platform",
//     username: "Digital Marketing Platform",
//     profileImage: "",
//     connected: true,
//     valid: true,
//     lastSync: "2026-08-26T08:50:00.000Z",
//   },

//   {
//     id: "dummy-youtube-001",
//     platform: "youtube",
//     pageName: "Digital Marketing Channel",
//     username: "@digitalmarketingchannel",
//     profileImage: "",
//     connected: true,
//     valid: true,
//     lastSync: "2026-08-26T08:30:00.000Z",
//   },
// ];

// export const DEMO_SOCIAL_ACCOUNTS = SOCIAL_ACCOUNT_DUMMY_DATA;

import { PLATFORM_IDS } from "../platforms/platformCapabilities";

// ============================================================
// SOCIAL ACCOUNT DUMMY DATA
// ============================================================
//
// Temporary frontend-only development fixture.
//
// This data represents connected social accounts belonging to
// specific organizations.
//
// IMPORTANT:
//
// - No API calls
// - No OAuth
// - No access tokens
// - No backend dependency
//
// The structure intentionally mirrors the future backend
// account model so the frontend can be integrated later
// without redesigning the UI data flow.
//
// ============================================================

export const SOCIAL_ACCOUNT_DUMMY_DATA = [
  // ==========================================================
  // ORGANIZATION: ORG001
  // ==========================================================

  {
    id: "dummy-org001-instagram-001",

    organizationId: "ORG001",

    platform: PLATFORM_IDS.INSTAGRAM,

    accountName: "Lumen Coffee",

    pageName: "Lumen Coffee",

    username: "@lumencoffee",

    profileImage: "",

    connected: true,

    valid: true,

    lastSync: "2026-08-26T09:30:00.000Z",
  },

  {
    id: "dummy-org001-instagram-002",

    organizationId: "ORG001",

    platform: PLATFORM_IDS.INSTAGRAM,

    accountName: "Lumen Coffee Reels",

    pageName: "Lumen Coffee Reels",

    username: "@lumencoffeereels",

    profileImage: "",

    connected: true,

    valid: true,

    lastSync: "2026-08-26T09:20:00.000Z",
  },

  {
    id: "dummy-org001-facebook-001",

    organizationId: "ORG001",

    platform: PLATFORM_IDS.FACEBOOK,

    accountName: "Lumen Coffee Co.",

    pageName: "Lumen Coffee Co.",

    username: "Lumen Coffee Co.",

    profileImage: "",

    connected: true,

    valid: true,

    lastSync: "2026-08-26T09:15:00.000Z",
  },

  // ==========================================================
  // ORGANIZATION: ORG002
  // ==========================================================

  {
    id: "dummy-org002-instagram-001",

    organizationId: "ORG002",

    platform: PLATFORM_IDS.INSTAGRAM,

    accountName: "Atlas Fitness",

    pageName: "Atlas Fitness",

    username: "@atlasfitness",

    profileImage: "",

    connected: true,

    valid: true,

    lastSync: "2026-08-26T08:50:00.000Z",
  },

  {
    id: "dummy-org002-instagram-002",

    organizationId: "ORG002",

    platform: PLATFORM_IDS.INSTAGRAM,

    accountName: "Atlas Fitness Training",

    pageName: "Atlas Fitness Training",

    username: "@atlastraining",

    profileImage: "",

    connected: true,

    valid: true,

    lastSync: "2026-08-26T08:40:00.000Z",
  },

  {
    id: "dummy-org002-facebook-001",

    organizationId: "ORG002",

    platform: PLATFORM_IDS.FACEBOOK,

    accountName: "Atlas Fitness",

    pageName: "Atlas Fitness",

    username: "Atlas Fitness",

    profileImage: "",

    connected: true,

    valid: true,

    lastSync: "2026-08-26T08:35:00.000Z",
  },

  {
    id: "dummy-org002-linkedin-001",

    organizationId: "ORG002",

    platform: PLATFORM_IDS.LINKEDIN,

    accountName: "Atlas Fitness",

    pageName: "Atlas Fitness",

    username: "Atlas Fitness",

    profileImage: "",

    connected: true,

    valid: true,

    lastSync: "2026-08-26T08:25:00.000Z",
  },

  // ==========================================================
  // ORGANIZATION: ORG003
  // ==========================================================

  {
    id: "dummy-org003-youtube-001",

    organizationId: "ORG003",

    platform: PLATFORM_IDS.YOUTUBE,

    accountName: "NorthPeak Outdoors",

    pageName: "NorthPeak Outdoors",

    username: "@northpeakoutdoors",

    profileImage: "",

    connected: true,

    valid: true,

    lastSync: "2026-08-26T08:10:00.000Z",
  },

  {
    id: "dummy-org003-youtube-002",

    organizationId: "ORG003",

    platform: PLATFORM_IDS.YOUTUBE,

    accountName: "NorthPeak Shorts",

    pageName: "NorthPeak Shorts",

    username: "@northpeakshorts",

    profileImage: "",

    connected: true,

    valid: true,

    lastSync: "2026-08-26T08:00:00.000Z",
  },

  {
    id: "dummy-org003-linkedin-001",

    organizationId: "ORG003",

    platform: PLATFORM_IDS.LINKEDIN,

    accountName: "NorthPeak Outdoors",

    pageName: "NorthPeak Outdoors",

    username: "NorthPeak Outdoors",

    profileImage: "",

    connected: true,

    valid: true,

    lastSync: "2026-08-26T07:50:00.000Z",
  },
];

// ============================================================
// BACKWARD-COMPATIBLE ALIAS
// ============================================================
//
// Existing Organization Overview code may still use:
//
// DEMO_SOCIAL_ACCOUNTS
//
// Keep this alias temporarily so existing UI code doesn't break.
//
// Once all dummy-data imports are removed, this alias and the
// entire dummy-data file can be deleted after backend integration.
// ============================================================

export const DEMO_SOCIAL_ACCOUNTS = SOCIAL_ACCOUNT_DUMMY_DATA;
