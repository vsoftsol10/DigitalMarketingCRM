import { PLATFORM_CAPABILITIES } from "../../constants/platforms/platformCapabilities.js";

import {
  MEDIA_TYPE,
} from "./media.utils.js";

const INSTAGRAM_IMAGE_MIN_ASPECT_RATIO = 0.75;
const INSTAGRAM_IMAGE_MAX_ASPECT_RATIO = 1.91;
// Accommodate integer pixel dimensions that represent a 3:4 image as 0.7498.
const INSTAGRAM_IMAGE_MIN_RATIO_TOLERANCE = 0.0002;

function getInstagramImageIssue(item, index) {
  if (item?.type !== MEDIA_TYPE.IMAGE) {
    return null;
  }

  if (item.dimensionsPending) {
    return null;
  }

  const label = `Instagram image ${index + 1} (${item.name || "unnamed"})`;
  if (item.dimensionsError) {
    return `${label} dimensions could not be read.`;
  }

  const imageMimeType = item.mime_type?.toLowerCase();
  if (imageMimeType && !["image/jpeg", "image/png"].includes(imageMimeType)) {
    return `${label} uses ${item.mime_type}; Instagram image publishing supports JPEG or PNG media.`;
  }

  const width = Number(item.width);
  const height = Number(item.height);
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    return `${label} dimensions are unavailable.`;
  }

  const aspectRatio = width / height;
  if (
    aspectRatio + INSTAGRAM_IMAGE_MIN_RATIO_TOLERANCE < INSTAGRAM_IMAGE_MIN_ASPECT_RATIO
    || aspectRatio > INSTAGRAM_IMAGE_MAX_ASPECT_RATIO
  ) {
    return `${label} is ${width}x${height} (ratio ${aspectRatio.toFixed(2)}); use a ratio between 0.75 and 1.91.`;
  }

  return null;
}

export function getInstagramImageIssues(media = []) {
  return (Array.isArray(media) ? media : [])
    .map((item, index) => getInstagramImageIssue(item, index))
    .filter(Boolean);
}

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

  if (
    platform === "INSTAGRAM"
    && ["POST", "CAROUSEL"].includes(String(contentType).toUpperCase())
    && analysis.hasImages
  ) {
    const imageIssues = getInstagramImageIssues(media);
    if (imageIssues.length) {
      return {
        available: false,
        reason: imageIssues[0],
      };
    }
  }

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
        reason: platform === "FACEBOOK"
          ? "Facebook posts do not support mixed image and video media."
          : "This content type does not support mixed image and video media.",
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
      reason: contentTypes.find((item) => item.reason)?.reason ||
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

export function retainSelectedAccountIds({
  selectedAccountIds = [],
  accounts = [],
  capabilityMap = new Map(),
}) {
  const selectableAccountIds = new Set(
    accounts
      .filter((account) => (
        (capabilityMap.get(account?.platform)?.available || account?.platform === "INSTAGRAM")
        && account?.connected !== false
        && account?.valid !== false
      ))
      .map((account) => account?.id)
      .filter(Boolean),
  );

  return selectedAccountIds.filter((accountId) => selectableAccountIds.has(accountId));
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
