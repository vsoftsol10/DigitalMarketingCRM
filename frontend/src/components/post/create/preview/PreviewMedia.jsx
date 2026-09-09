import { Box, IconButton, Stack, Typography } from "@mui/material";

import ChevronLeftRoundedIcon from "@mui/icons-material/ChevronLeftRounded";
import ChevronRightRoundedIcon from "@mui/icons-material/ChevronRightRounded";
import ImageOutlinedIcon from "@mui/icons-material/ImageOutlined";
import VideocamOutlinedIcon from "@mui/icons-material/VideocamOutlined";

import { useEffect, useMemo, useState } from "react";

import { TYPOGRAPHY } from "../../../../theme/typography";

// ============================================================
// PLATFORM
// ============================================================

const PLATFORM = {
  INSTAGRAM: "INSTAGRAM",
  FACEBOOK: "FACEBOOK",
  LINKEDIN: "LINKEDIN",
  YOUTUBE: "YOUTUBE",
};

// ============================================================
// CONTENT TYPES
// ============================================================

const CONTENT_TYPE = {
  POST: "POST",
  REEL: "REEL",
  STORY: "STORY",

  IMAGE: "IMAGE",
  MULTI_IMAGE: "MULTI_IMAGE",

  VIDEO: "VIDEO",
  SHORT: "SHORT",
};

// ============================================================
// PREVIEW MODES
// ============================================================

const PREVIEW_MODE = {
  SINGLE: "SINGLE",
  MULTI: "MULTI",
  IMAGE_ONLY: "IMAGE_ONLY",
  VIDEO_ONLY: "VIDEO_ONLY",
};

// ============================================================
// COMPONENT
// ============================================================

export default function PreviewMedia({
  media = [],
  platform = "",
  contentType = "",
}) {
  const [activeIndex, setActiveIndex] = useState(0);

  // ==========================================================
  // NORMALIZE MEDIA
  // ==========================================================

  const normalizedMedia = useMemo(() => {
    if (!Array.isArray(media)) {
      return [];
    }

    return media.filter(Boolean);
  }, [media]);

  // ==========================================================
  // DETERMINE PREVIEW MODE
  // ==========================================================

  const previewMode = getPreviewMode({
    platform,
    contentType,
  });

  // ==========================================================
  // MEDIA FOR THIS PREVIEW
  // ==========================================================

  const displayMedia = useMemo(() => {
    switch (previewMode) {
      case PREVIEW_MODE.SINGLE:
        return normalizedMedia.slice(0, 1);

      case PREVIEW_MODE.IMAGE_ONLY:
        return normalizedMedia.filter((item) => item?.type === "IMAGE");

      case PREVIEW_MODE.VIDEO_ONLY:
        return normalizedMedia
          .filter((item) => item?.type === "VIDEO")
          .slice(0, 1);

      case PREVIEW_MODE.MULTI:
      default:
        return normalizedMedia;
    }
  }, [normalizedMedia, previewMode]);

  // ==========================================================
  // RESET INDEX WHEN PLATFORM / TYPE CHANGES
  // ==========================================================

  useEffect(() => {
    setActiveIndex(0);
  }, [platform, contentType]);

  // ==========================================================
  // KEEP INDEX VALID WHEN MEDIA CHANGES
  // ==========================================================

  useEffect(() => {
    if (!displayMedia.length) {
      setActiveIndex(0);
      return;
    }

    setActiveIndex((currentIndex) =>
      Math.min(currentIndex, displayMedia.length - 1),
    );
  }, [displayMedia.length]);

  // ==========================================================
  // NO MEDIA
  // ==========================================================

  if (!normalizedMedia.length) {
    return (
      <Box
        sx={{
          height: 320,

          bgcolor: "#F8FAFC",

          display: "flex",
          flexDirection: "column",

          justifyContent: "center",
          alignItems: "center",

          gap: 1,
        }}
      >
        <ImageOutlinedIcon
          sx={{
            fontSize: 42,
            color: "#94A3B8",
          }}
        />

        <Typography sx={TYPOGRAPHY.bodySmall}>
          Upload media to preview
        </Typography>
      </Box>
    );
  }

  // ==========================================================
  // NO COMPATIBLE MEDIA
  // ==========================================================

  if (!displayMedia.length) {
    return (
      <Box
        sx={{
          height: 320,

          bgcolor: "#F8FAFC",

          display: "flex",
          flexDirection: "column",

          alignItems: "center",
          justifyContent: "center",

          gap: 1,

          px: 3,

          textAlign: "center",
        }}
      >
        <VideocamOutlinedIcon
          sx={{
            fontSize: 40,
            color: "#94A3B8",
          }}
        />

        <Typography
          sx={{
            ...TYPOGRAPHY.bodySmall,
            color: "#64748B",
          }}
        >
          No compatible media available for this content type.
        </Typography>
      </Box>
    );
  }

  // ==========================================================
  // ACTIVE MEDIA
  // ==========================================================

  const activeMedia = displayMedia[activeIndex];

  const isImage = activeMedia?.type === "IMAGE";

  const isVideo = activeMedia?.type === "VIDEO";

  const hasMultiple = displayMedia.length > 1;

  // ==========================================================
  // NAVIGATION
  // ==========================================================

  const canGoPrevious = activeIndex > 0;

  const canGoNext = activeIndex < displayMedia.length - 1;

  function handlePrevious() {
    if (!canGoPrevious) {
      return;
    }

    setActiveIndex((currentIndex) => currentIndex - 1);
  }

  function handleNext() {
    if (!canGoNext) {
      return;
    }

    setActiveIndex((currentIndex) => currentIndex + 1);
  }

  // ==========================================================
  // VERTICAL CONTENT
  // ==========================================================

  // const isVertical = isVerticalContentType(platform, contentType);
  const isVertical = isVerticalContentType(contentType);

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <Box
      sx={{
        position: "relative",

        width: "100%",

        /*
         * Feed content:
         * 1:1
         *
         * Story / Reel / Short:
         * 9:16
         */
        aspectRatio: isVertical ? "9 / 16" : "1 / 1",

        maxHeight: 520,

        bgcolor: isVideo ? "#000000" : "#F8FAFC",

        overflow: "hidden",
      }}
    >
      {/* ======================================================
          IMAGE
      ====================================================== */}

      {isImage && activeMedia?.preview && (
        <Box
          component="img"
          src={activeMedia.preview}
          alt={activeMedia.name || `Media ${activeIndex + 1}`}
          sx={{
            width: "100%",
            height: "100%",

            display: "block",

            objectFit: "cover",
          }}
        />
      )}

      {/* ======================================================
          VIDEO
      ====================================================== */}

      {isVideo && activeMedia?.preview && (
        <Box
          component="video"
          src={activeMedia.preview}
          controls
          playsInline
          preload="metadata"
          sx={{
            width: "100%",
            height: "100%",

            display: "block",

            objectFit: "cover",

            bgcolor: "#000000",
          }}
        />
      )}

      {/* ======================================================
          FALLBACK
      ====================================================== */}

      {!activeMedia?.preview && (
        <Stack
          sx={{
            width: "100%",
            height: "100%",

            alignItems: "center",
            justifyContent: "center",

            gap: 1,
          }}
        >
          {isVideo ? (
            <VideocamOutlinedIcon
              sx={{
                fontSize: 42,
                color: "#94A3B8",
              }}
            />
          ) : (
            <ImageOutlinedIcon
              sx={{
                fontSize: 42,
                color: "#94A3B8",
              }}
            />
          )}

          <Typography sx={TYPOGRAPHY.bodySmall}>
            Media preview unavailable
          </Typography>
        </Stack>
      )}

      {/* ======================================================
          MEDIA COUNT
      ====================================================== */}

      {hasMultiple && (
        <Box
          sx={{
            position: "absolute",

            top: 12,
            right: 12,

            minWidth: 42,
            height: 26,

            px: 1,

            borderRadius: "999px",

            bgcolor: "rgba(15, 23, 42, 0.68)",

            color: "#FFFFFF",

            display: "flex",
            alignItems: "center",
            justifyContent: "center",

            backdropFilter: "blur(4px)",

            zIndex: 2,
          }}
        >
          <Typography
            sx={{
              fontSize: 11.5,
              fontWeight: 600,
              lineHeight: 1,
            }}
          >
            {activeIndex + 1} / {displayMedia.length}
          </Typography>
        </Box>
      )}

      {/* ======================================================
          PREVIOUS
      ====================================================== */}

      {hasMultiple && canGoPrevious && (
        <IconButton
          size="small"
          aria-label="Previous media"
          onClick={handlePrevious}
          sx={{
            position: "absolute",

            left: 10,
            top: "50%",

            transform: "translateY(-50%)",

            width: 34,
            height: 34,

            bgcolor: "rgba(255, 255, 255, 0.9)",

            border: "1px solid rgba(226, 232, 240, 0.9)",

            color: "#334155",

            boxShadow: "0 2px 8px rgba(15, 23, 42, 0.12)",

            zIndex: 2,

            "&:hover": {
              bgcolor: "#FFFFFF",
            },
          }}
        >
          <ChevronLeftRoundedIcon
            sx={{
              fontSize: 20,
            }}
          />
        </IconButton>
      )}

      {/* ======================================================
          NEXT
      ====================================================== */}

      {hasMultiple && canGoNext && (
        <IconButton
          size="small"
          aria-label="Next media"
          onClick={handleNext}
          sx={{
            position: "absolute",

            right: 10,
            top: "50%",

            transform: "translateY(-50%)",

            width: 34,
            height: 34,

            bgcolor: "rgba(255, 255, 255, 0.9)",

            border: "1px solid rgba(226, 232, 240, 0.9)",

            color: "#334155",

            boxShadow: "0 2px 8px rgba(15, 23, 42, 0.12)",

            zIndex: 2,

            "&:hover": {
              bgcolor: "#FFFFFF",
            },
          }}
        >
          <ChevronRightRoundedIcon
            sx={{
              fontSize: 20,
            }}
          />
        </IconButton>
      )}

      {/* ======================================================
          DOT INDICATORS
      ====================================================== */}

      {hasMultiple && (
        <Box
          sx={{
            position: "absolute",

            left: 0,
            right: 0,
            bottom: 10,

            display: "flex",

            justifyContent: "center",
            alignItems: "center",

            gap: 0.6,

            zIndex: 2,
          }}
        >
          {displayMedia.map((item, index) => (
            <Box
              key={item?.id || index}
              component="button"
              type="button"
              aria-label={`Show media ${index + 1}`}
              onClick={() => setActiveIndex(index)}
              sx={{
                width: index === activeIndex ? 18 : 6,

                height: 6,

                p: 0,

                border: "none",

                borderRadius: "999px",

                bgcolor:
                  index === activeIndex ? "#FFFFFF" : "rgba(255,255,255,0.55)",

                cursor: "pointer",

                transition: "width .2s ease, background-color .2s ease",

                boxShadow: "0 1px 3px rgba(15,23,42,0.18)",
              }}
            />
          ))}
        </Box>
      )}
    </Box>
  );
}

// ============================================================
// GET PREVIEW MODE
// ============================================================

function getPreviewMode({ platform, contentType }) {
  // ==========================================================
  // INSTAGRAM
  // ==========================================================

  if (platform === PLATFORM.INSTAGRAM) {
    if (contentType === CONTENT_TYPE.STORY) {
      return PREVIEW_MODE.SINGLE;
    }

    if (contentType === CONTENT_TYPE.REEL) {
      return PREVIEW_MODE.VIDEO_ONLY;
    }

    if (contentType === CONTENT_TYPE.POST) {
      return PREVIEW_MODE.MULTI;
    }
  }

  // ==========================================================
  // FACEBOOK
  // ==========================================================

  if (platform === PLATFORM.FACEBOOK) {
    if (contentType === CONTENT_TYPE.STORY) {
      return PREVIEW_MODE.SINGLE;
    }

    if (contentType === CONTENT_TYPE.REEL) {
      return PREVIEW_MODE.VIDEO_ONLY;
    }

    if (contentType === CONTENT_TYPE.POST) {
      return PREVIEW_MODE.MULTI;
    }
  }

  // ==========================================================
  // LINKEDIN
  // ==========================================================

  if (platform === PLATFORM.LINKEDIN) {
    if (contentType === CONTENT_TYPE.IMAGE) {
      return PREVIEW_MODE.IMAGE_ONLY;
    }

    if (contentType === CONTENT_TYPE.MULTI_IMAGE) {
      return PREVIEW_MODE.IMAGE_ONLY;
    }

    if (contentType === CONTENT_TYPE.VIDEO) {
      return PREVIEW_MODE.VIDEO_ONLY;
    }
  }

  // ==========================================================
  // YOUTUBE
  // ==========================================================

  if (platform === PLATFORM.YOUTUBE) {
    if (
      contentType === CONTENT_TYPE.VIDEO ||
      contentType === CONTENT_TYPE.SHORT
    ) {
      return PREVIEW_MODE.VIDEO_ONLY;
    }
  }

  // ==========================================================
  // DEFAULT
  // ==========================================================

  return PREVIEW_MODE.MULTI;
}

// ============================================================
// VERTICAL CONTENT
// ============================================================

function isVerticalContentType(contentType) {
  return (
    contentType === CONTENT_TYPE.REEL ||
    contentType === CONTENT_TYPE.STORY ||
    contentType === CONTENT_TYPE.SHORT
  );
}
