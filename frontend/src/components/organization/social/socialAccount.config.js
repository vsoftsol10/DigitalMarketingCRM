// ============================================================
// SOCIAL ACCOUNT UI CONFIGURATION
// ============================================================
//
// This file contains UI-only configuration and demo data.
//
// IMPORTANT:
// - No API calls
// - No OAuth logic
// - No backend dependency
//
// Later, the dummy accounts can be replaced by useSocialAccounts()
// without changing the UI components.
// ============================================================

import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import YouTubeIcon from "@mui/icons-material/YouTube";
import XIcon from "@mui/icons-material/X";

// ============================================================
// PLATFORM CONFIGURATION
// ============================================================

export const SOCIAL_PLATFORM_CONFIG = {
  instagram: {
    id: "instagram",
    name: "Instagram",
    icon: InstagramIcon,
    backgroundColor: "#FDF2F8",
    iconColor: "#E1306C",
  },

  facebook: {
    id: "facebook",
    name: "Facebook",
    icon: FacebookRoundedIcon,
    backgroundColor: "#EFF6FF",
    iconColor: "#1877F2",
  },

  linkedin: {
    id: "linkedin",
    name: "LinkedIn",
    icon: LinkedInIcon,
    backgroundColor: "#EFF6FF",
    iconColor: "#0A66C2",
  },

  threads: {
    id: "threads",
    name: "Threads",
    icon: SmartToyOutlinedIcon,
    backgroundColor: "#F5F5F5",
    iconColor: "#111827",
  },

  x: {
    id: "x",
    name: "X",
    icon: XIcon,
    backgroundColor: "#F5F5F5",
    iconColor: "#111827",
  },

  youtube: {
    id: "youtube",
    name: "YouTube",
    icon: YouTubeIcon,
    backgroundColor: "#FEF2F2",
    iconColor: "#FF0000",
  },
};

// ============================================================
// AVAILABLE SOCIAL PLATFORMS
// ============================================================

export const SOCIAL_ACCOUNT_PLATFORMS = Object.values(SOCIAL_PLATFORM_CONFIG);

// ============================================================
// DEMO / DUMMY CONNECTED ACCOUNTS
// ============================================================
//
// This is temporary UI data.
//
// Later:
//
// API
//   ↓
// useSocialAccounts()
//   ↓
// normalized account model
//   ↓
// SocialAccountsSection
//
// The UI components should not need to change.
// ============================================================

export const DEMO_SOCIAL_ACCOUNTS = [
  {
    id: "demo-instagram-001",
    platform: "instagram",

    pageName: "Digital Marketing",
    username: "@digitalmarketing",

    profileImage: "",

    connected: true,
    valid: true,

    lastSync: "2026-08-26T09:30:00",
  },

  {
    id: "demo-facebook-001",
    platform: "facebook",

    pageName: "Digital Marketing Platform",
    username: "Digital Marketing Platform",

    profileImage: "",

    connected: true,
    valid: true,

    lastSync: "2026-08-26T09:15:00",
  },
];

// ============================================================
// PLATFORM HELPERS
// ============================================================

export function getSocialPlatformConfig(platform) {
  if (!platform) {
    return null;
  }

  return SOCIAL_PLATFORM_CONFIG[platform] || null;
}

// ============================================================
// ACCOUNT NORMALIZER
// ============================================================
//
// Keeps the UI independent from backend field naming.
//
// Example backend:
// page_name
//
// Frontend:
// pageName
//
// Later the service mapper can provide the same shape.
// ============================================================

export function normalizeSocialAccount(account) {
  if (!account) {
    return null;
  }

  const platform = account.platform;

  return {
    id: account.id,

    platform,

    pageName:
      account.pageName ?? account.page_name ?? account.account_name ?? "",

    username: account.username ?? "",

    profileImage: account.profileImage ?? account.profile_image ?? "",

    connected: account.connected ?? account.status === "connected" ?? false,

    valid: account.valid ?? account.is_valid ?? true,

    lastSync:
      account.lastSync ?? account.last_sync ?? account.last_synced_at ?? null,
  };
}

// ============================================================
// ACCOUNT COLLECTION NORMALIZER
// ============================================================

export function normalizeSocialAccounts(accounts) {
  if (!Array.isArray(accounts)) {
    return [];
  }

  return accounts.map(normalizeSocialAccount).filter(Boolean);
}

// ============================================================
// CONNECTED PLATFORM HELPERS
// ============================================================

export function getConnectedPlatforms(accounts) {
  return new Set(
    normalizeSocialAccounts(accounts)
      .filter((account) => account.connected)
      .map((account) => account.platform)
      .filter(Boolean),
  );
}
