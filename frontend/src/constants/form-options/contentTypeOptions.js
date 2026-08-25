export const CONTENT_TYPE_OPTIONS_BY_PLATFORM = {
  INSTAGRAM: [
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
  ],

  FACEBOOK: [
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
  ],

  YOUTUBE: [
    {
      value: "SHORT",
      label: "Short",
    },
    {
      value: "VIDEO",
      label: "Video",
    },
  ],

  LINKEDIN: [
    {
      value: "POST",
      label: "Post",
    },
    {
      value: "CAROUSEL",
      label: "Carousel",
    },
    {
      value: "VIDEO",
      label: "Video",
    },
  ],

  X: [
    {
      value: "POST",
      label: "Post",
    },
    {
      value: "VIDEO",
      label: "Video",
    },
  ],
};

export function getContentTypeOptions(platform) {
  if (!platform) {
    return [];
  }

  return CONTENT_TYPE_OPTIONS_BY_PLATFORM[platform] || [];
}
