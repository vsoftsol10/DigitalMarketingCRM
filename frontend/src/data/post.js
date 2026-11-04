// export const CREATE_POST = {
//   // ==========================================
//   // ORGANIZATIONS
//   // ==========================================

//   organizations: [
//     {
//       id: "ORG001",
//       name: "Lumen Coffee Co.",
//     },
//     {
//       id: "ORG002",
//       name: "Atlas Fitness",
//     },
//     {
//       id: "ORG003",
//       name: "NorthPeak Outdoors",
//     },
//   ],

//   // ==========================================
//   // SOCIAL PLATFORMS
//   // ==========================================

//   platforms: [
//     {
//       id: "INSTAGRAM",
//       name: "Instagram",
//       icon: "instagram",
//       connected: true,
//       content_types: ["POST", "REEL", "STORY", "CAROUSEL"],
//     },

//     {
//       id: "FACEBOOK",
//       name: "Facebook",
//       icon: "facebook",
//       connected: true,
//       content_types: ["POST", "REEL", "STORY"],
//     },

//     {
//       id: "LINKEDIN",
//       name: "LinkedIn",
//       icon: "linkedin",
//       connected: true,
//       content_types: ["POST"],
//     },

//     {
//       id: "YOUTUBE",
//       name: "YouTube",
//       icon: "youtube",
//       connected: true,
//       content_types: ["SHORT", "VIDEO"],
//     },

//     {
//       id: "THREADS",
//       name: "Threads",
//       icon: "threads",
//       connected: false,
//       content_types: ["POST"],
//     },

//     {
//       id: "X",
//       name: "X",
//       icon: "x",
//       connected: false,
//       content_types: ["POST"],
//     },
//   ],

//   // ==========================================
//   // MEDIA CONFIG
//   // ==========================================

//   media: {
//     accepted_types: ["image/jpeg", "image/png", "image/webp", "video/mp4"],

//     accepted_extensions: [".jpg", ".jpeg", ".png", ".webp", ".mp4"],

//     max_files: 10,

//     max_file_size_mb: 50,

//     allow_multiple: true,
//   },

//   // ==========================================
//   // PUBLISHING
//   // ==========================================

//   publishing: {
//     default_publish_type: "NOW",

//     timezones: [
//       {
//         value: "Asia/Kolkata",
//         label: "Asia / Kolkata (IST)",
//       },
//     ],
//   },

//   // ==========================================
//   // AI
//   // ==========================================

//   ai: {
//     enabled: true,
//   },

//   // ==========================================
//   // PREVIEW
//   // ==========================================

//   preview: {
//     default_platform: "INSTAGRAM",
//   },
// };

export const CREATE_POST = {
  // ==========================================
  // ORGANIZATIONS
  // ==========================================

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

  // ==========================================
  // SOCIAL PLATFORMS
  // ==========================================
  //
  // This is platform configuration only.
  //
  // Connected accounts are organization-specific
  // runtime data and must NOT be stored here.
  //
  // Supported platforms:
  // Instagram
  // Facebook
  // LinkedIn
  // YouTube
  //
  // ==========================================

  platforms: [
    {
      id: "INSTAGRAM",
      name: "Instagram",
      icon: "instagram",
      content_types: ["POST", "REEL", "STORY", "CAROUSEL"],
    },

    {
      id: "FACEBOOK",
      name: "Facebook",
      icon: "facebook",
      content_types: ["POST", "REEL", "STORY"],
    },

    {
      id: "LINKEDIN",
      name: "LinkedIn",
      icon: "linkedin",
      content_types: ["POST"],
    },

    {
      id: "YOUTUBE",
      name: "YouTube",
      icon: "youtube",
      content_types: ["SHORT", "VIDEO"],
    },
  ],

  // ==========================================
  // MEDIA CONFIG
  // ==========================================

  media: {
    accepted_types: [
      "image/jpeg",
      "image/png",
      "image/webp",
      "video/mp4",
      "video/quicktime",
    ],

    accepted_extensions: [
      ".jpg",
      ".jpeg",
      ".png",
      ".webp",
      ".mp4",
      ".mov",
    ],

    max_files: 10,

    // The authoritative size limit is returned by the upload-session API.
    // Keeping this unset prevents an arbitrary small browser-only ceiling.
    max_file_size_mb: null,

    allow_multiple: true,
  },

  // ==========================================
  // PUBLISHING
  // ==========================================

  publishing: {
    default_publish_type: "NOW",

    timezones: [
      {
        value: "Asia/Kolkata",
        label: "Asia / Kolkata (IST)",
      },
    ],
  },

  // ==========================================
  // AI
  // ==========================================

  ai: {
    enabled: true,
  },

  // ==========================================
  // PREVIEW
  // ==========================================

  preview: {
    default_platform: "INSTAGRAM",
  },
};
