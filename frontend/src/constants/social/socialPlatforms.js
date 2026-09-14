export const SOCIAL_PLATFORMS = [
  {
    id: "facebook",
    name: "Facebook",
    description: "Facebook Page",
    icon: "facebook",
    backgroundColor: "#EFF6FF",
    iconColor: "#1877F2",
  },
  {
    id: "instagram",
    name: "Instagram",
    description: "Professional account",
    icon: "instagram",
    backgroundColor: "#FDF2F8",
    iconColor: "#E1306C",
  },
  {
    id: "linkedin",
    name: "LinkedIn",
    description: "Coming soon",
    icon: "linkedin",
    backgroundColor: "#EFF6FF",
    iconColor: "#0A66C2",
    comingSoon: true,
  },
  {
    id: "youtube",
    name: "YouTube",
    description: "Coming soon",
    icon: "youtube",
    backgroundColor: "#FEF2F2",
    iconColor: "#FF0000",
    comingSoon: true,
  },
];

export const SOCIAL_PLATFORM_IDS = {
  FACEBOOK: "facebook",
  INSTAGRAM: "instagram",
  LINKEDIN: "linkedin",
  YOUTUBE: "youtube",
};

export const SOCIAL_PLATFORM_LABELS = {
  facebook: "Facebook",
  instagram: "Instagram",
  linkedin: "LinkedIn",
  youtube: "YouTube",
};

export const SOCIAL_PLATFORM_DESCRIPTIONS = {
  facebook: "Facebook Page",
  instagram: "Professional account",
  linkedin: "Coming soon",
  youtube: "Coming soon",
};

export const getSocialPlatform = (platformId) =>
  SOCIAL_PLATFORMS.find((platform) => platform.id === platformId);

export const getSocialPlatformLabel = (platformId) =>
  SOCIAL_PLATFORM_LABELS[platformId] || platformId;

export const isFacebookPlatform = (platformId) =>
  platformId === SOCIAL_PLATFORM_IDS.FACEBOOK;

export const isInstagramPlatform = (platformId) =>
  platformId === SOCIAL_PLATFORM_IDS.INSTAGRAM;
