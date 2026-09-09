import { MEDIA_TYPE } from "../../utils/post/media.utils";

export const PLATFORM_IDS = {
  INSTAGRAM: "INSTAGRAM",
  FACEBOOK: "FACEBOOK",
  LINKEDIN: "LINKEDIN",
  YOUTUBE: "YOUTUBE",
};

export const CONTENT_TYPES = {
  INSTAGRAM_POST: "POST",
  INSTAGRAM_REEL: "REEL",
  INSTAGRAM_STORY: "STORY",

  FACEBOOK_POST: "POST",
  FACEBOOK_REEL: "REEL",
  FACEBOOK_STORY: "STORY",

  LINKEDIN_IMAGE: "IMAGE",
  LINKEDIN_MULTI_IMAGE: "MULTI_IMAGE",
  LINKEDIN_VIDEO: "VIDEO",

  YOUTUBE_VIDEO: "VIDEO",
  YOUTUBE_SHORT: "SHORT",
};

/*
 * IMPORTANT
 *
 * These are frontend composer capabilities.
 *
 * Actual provider publishing APIs will be validated again
 * in the backend integration layer before publishing.
 */

export const PLATFORM_CAPABILITIES = {
  [PLATFORM_IDS.INSTAGRAM]: {
    platform: PLATFORM_IDS.INSTAGRAM,

    contentTypes: {
      POST: {
        label: "Post",

        rules: {
          image: {
            min: 1,
            max: 10,
            multiple: true,
          },

          video: {
            min: 1,
            max: 1,
            multiple: false,
          },

          mixed: {
            min: 2,
            max: 10,
            multiple: true,
          },
        },
      },

      REEL: {
        label: "Reel",

        rules: {
          video: {
            min: 1,
            max: 1,
            multiple: false,
          },
        },
      },

      STORY: {
        label: "Story",

        rules: {
          image: {
            min: 1,
            max: 1,
            multiple: false,
          },

          video: {
            min: 1,
            max: 1,
            multiple: false,
          },
        },
      },
    },
  },

  [PLATFORM_IDS.FACEBOOK]: {
    platform: PLATFORM_IDS.FACEBOOK,

    contentTypes: {
      POST: {
        label: "Post",

        rules: {
          image: {
            min: 1,
            max: 10,
            multiple: true,
          },

          video: {
            min: 1,
            max: 1,
            multiple: false,
          },

          mixed: {
            min: 2,
            max: 10,
            multiple: true,
          },
        },
      },

      REEL: {
        label: "Reel",

        rules: {
          video: {
            min: 1,
            max: 1,
            multiple: false,
          },
        },
      },

      STORY: {
        label: "Story",

        rules: {
          image: {
            min: 1,
            max: 1,
            multiple: false,
          },

          video: {
            min: 1,
            max: 1,
            multiple: false,
          },
        },
      },
    },
  },

  [PLATFORM_IDS.LINKEDIN]: {
    platform: PLATFORM_IDS.LINKEDIN,

    contentTypes: {
      IMAGE: {
        label: "Image",

        rules: {
          image: {
            min: 1,
            max: 1,
            multiple: false,
          },
        },
      },

      MULTI_IMAGE: {
        label: "Multi Image",

        rules: {
          image: {
            min: 2,
            max: 20,
            multiple: true,
          },
        },
      },

      VIDEO: {
        label: "Video",

        rules: {
          video: {
            min: 1,
            max: 1,
            multiple: false,
          },
        },
      },
    },
  },

  [PLATFORM_IDS.YOUTUBE]: {
    platform: PLATFORM_IDS.YOUTUBE,

    contentTypes: {
      VIDEO: {
        label: "Video",

        rules: {
          video: {
            min: 1,
            max: 1,
            multiple: false,
          },
        },
      },

      SHORT: {
        label: "Short",

        rules: {
          video: {
            min: 1,
            max: 1,
            multiple: false,
          },
        },
      },
    },
  },
};