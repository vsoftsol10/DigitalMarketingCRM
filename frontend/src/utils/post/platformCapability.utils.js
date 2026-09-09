import {
  CONTENT_TYPES,
  PLATFORM_CAPABILITIES,
} from "../../constants/platforms/platformCapabilities";

import {
  MEDIA_TYPE,
} from "./media.utils";

// ============================================================
// MEDIA ANALYSIS
// ============================================================

export function analyzeMedia(media = []) {
  const items = Array.isArray(media)
    ? media
    : [];

  const imageCount = items.filter(
    (item) => item?.type === MEDIA_TYPE.IMAGE,
  ).length;

  const videoCount = items.filter(
    (item) => item?.type === MEDIA_TYPE.VIDEO,
  ).length;

  return {
    total: items.length,

    imageCount,

    videoCount,

    hasImages: imageCount > 0,

    hasVideos: videoCount > 0,

    isImageOnly:
      imageCount > 0 && videoCount === 0,

    isVideoOnly:
      videoCount > 0 && imageCount === 0,

    isMixed:
      imageCount > 0 && videoCount > 0,
  };
}

// ============================================================
// RULE MATCHING
// ============================================================

function matchesRule({
  count,
  rule,
}) {
  if (!rule) {
    return false;
  }

  if (count < rule.min) {
    return false;
  }

  if (count > rule.max) {
    return false;
  }

  return true;
}

// ============================================================
// CONTENT TYPE AVAILABILITY
// ============================================================

export function evaluateContentType({
  platform,
  contentType,
  media = [],
}) {
  const platformConfig =
    PLATFORM_CAPABILITIES[platform];

  if (!platformConfig) {
    return {
      available: false,
      reason: "Unsupported platform.",
    };
  }

  const contentConfig =
    platformConfig.contentTypes[
      contentType
    ];

  if (!contentConfig) {
    return {
      available: false,
      reason: "Unsupported content type.",
    };
  }

  const analysis = analyzeMedia(media);

  /*
   * Empty media:
   * content type exists but cannot yet be selected.
   */

  if (analysis.total === 0) {
    return {
      available: false,
      reason:
        "Upload media to determine whether this content type is available.",
    };
  }

  /*
   * IMAGE ONLY
   */

  if (analysis.isImageOnly) {
    const rule =
      contentConfig.rules.image;

    if (!rule) {
      return {
        available: false,
        reason:
          "This content type does not support image media.",
      };
    }

    if (
      !matchesRule({
        count: analysis.imageCount,
        rule,
      })
    ) {
      return {
        available: false,
        reason: getImageCountReason({
          count: analysis.imageCount,
          rule,
        }),
      };
    }

    return {
      available: true,
      reason: "",
    };
  }

  /*
   * VIDEO ONLY
   */

  if (analysis.isVideoOnly) {
    const rule =
      contentConfig.rules.video;

    if (!rule) {
      return {
        available: false,
        reason:
          "This content type does not support video media.",
      };
    }

    if (
      !matchesRule({
        count: analysis.videoCount,
        rule,
      })
    ) {
      return {
        available: false,
        reason: getVideoCountReason({
          count: analysis.videoCount,
          rule,
        }),
      };
    }

    return {
      available: true,
      reason: "",
    };
  }

  /*
   * MIXED MEDIA
   */

  if (analysis.isMixed) {
    const rule =
      contentConfig.rules.mixed;

    if (!rule) {
      return {
        available: false,
        reason:
          "This content type does not support mixed image and video media.",
      };
    }

    if (
      analysis.total < rule.min ||
      analysis.total > rule.max
    ) {
      return {
        available: false,
        reason: getMixedMediaReason({
          count: analysis.total,
          rule,
        }),
      };
    }

    return {
      available: true,
      reason: "",
    };
  }

  return {
    available: false,
    reason:
      "The selected media combination is not supported.",
  };
}

// ============================================================
// AVAILABLE CONTENT TYPES
// ============================================================

export function getContentTypeStates({
  platform,
  media = [],
}) {
  const platformConfig =
    PLATFORM_CAPABILITIES[platform];

  if (!platformConfig) {
    return [];
  }

  return Object.entries(
    platformConfig.contentTypes,
  ).map(
    ([value, config]) => {
      const evaluation =
        evaluateContentType({
          platform,
          contentType: value,
          media,
        });

      return {
        value,

        label: config.label,

        available:
          evaluation.available,

        disabled:
          !evaluation.available,

        reason:
          evaluation.reason,
      };
    },
  );
}

// ============================================================
// PLATFORM AVAILABILITY
// ============================================================

export function evaluatePlatform({
  platform,
  media = [],
}) {
  const platformConfig =
    PLATFORM_CAPABILITIES[platform];

  if (!platformConfig) {
    return {
      available: false,
      reason: "Unsupported platform.",
    };
  }

  const contentTypes =
    getContentTypeStates({
      platform,
      media,
    });

  const availableContentTypes =
    contentTypes.filter(
      (item) => item.available,
    );

  if (!media.length) {
    return {
      available: false,
      reason:
        "Upload media to determine platform compatibility.",
      contentTypes,
    };
  }

  if (!availableContentTypes.length) {
    return {
      available: false,
      reason:
        "The selected media combination is not supported on this platform.",
      contentTypes,
    };
  }

  return {
    available: true,
    reason: "",
    contentTypes,
  };
}

// ============================================================
// ALL PLATFORM STATES
// ============================================================

export function getPlatformStates({
  media = [],
}) {
  return Object.values(
    PLATFORM_CAPABILITIES,
  ).map((platform) => {
    const evaluation =
      evaluatePlatform({
        platform: platform.platform,
        media,
      });

    return {
      platform:
        platform.platform,

      available:
        evaluation.available,

      disabled:
        !evaluation.available,

      reason:
        evaluation.reason,

      contentTypes:
        evaluation.contentTypes,
    };
  });
}

// ============================================================
// REASONS
// ============================================================

function getImageCountReason({
  count,
  rule,
}) {
  if (count < rule.min) {
    return `This content type requires at least ${rule.min} image${
      rule.min > 1 ? "s" : ""
    }.`;
  }

  if (count > rule.max) {
    return `This content type supports a maximum of ${rule.max} images.`;
  }

  return "Unsupported image selection.";
}

function getVideoCountReason({
  count,
  rule,
}) {
  if (count < rule.min) {
    return "A video is required.";
  }

  if (count > rule.max) {
    return `This content type supports a maximum of ${rule.max} video${
      rule.max > 1 ? "s" : ""
    }.`;
  }

  return "Unsupported video selection.";
}

function getMixedMediaReason({
  count,
  rule,
}) {
  if (count < rule.min) {
    return `At least ${rule.min} media items are required.`;
  }

  if (count > rule.max) {
    return `A maximum of ${rule.max} media items is supported.`;
  }

  return "This mixed-media combination is not supported.";
}