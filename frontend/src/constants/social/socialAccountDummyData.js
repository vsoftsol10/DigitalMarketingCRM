// ============================================================
// SOCIAL ACCOUNT DUMMY DATA
// ============================================================
//
// Temporary frontend-only data.
//
// This file is used only for UI preview/testing.
//
// No API
// No OAuth
// No access token
// No backend dependency
//
// Later, when backend integration is ready, this file can be
// removed and SocialAccountsSection can use useSocialAccounts().
//
// ============================================================

export const SOCIAL_ACCOUNT_DUMMY_DATA = [
  {
    id: "dummy-instagram-001",

    platform: "instagram",

    pageName: "Digital Marketing",

    username: "@digitalmarketing",

    profileImage: "",

    connected: true,

    valid: true,

    lastSync: "2026-08-26T09:30:00.000Z",
  },

  {
    id: "dummy-facebook-001",

    platform: "facebook",

    pageName: "Digital Marketing Platform",

    username: "Digital Marketing Platform",

    profileImage: "",

    connected: true,

    valid: true,

    lastSync: "2026-08-26T09:15:00.000Z",
  },
];

// ============================================================
// BACKWARD-COMPATIBLE ALIAS
// ============================================================
//
// OrganizationOverview currently imports:
//
// DEMO_SOCIAL_ACCOUNTS
//
// So expose the same data using that name.
//
// This avoids duplicating the dummy data.
//

export const DEMO_SOCIAL_ACCOUNTS =
  SOCIAL_ACCOUNT_DUMMY_DATA;