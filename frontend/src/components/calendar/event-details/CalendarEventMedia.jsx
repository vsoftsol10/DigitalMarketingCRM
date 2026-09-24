import { Box, IconButton, Stack, Typography } from "@mui/material";

import ChevronLeftRoundedIcon from "@mui/icons-material/ChevronLeftRounded";
import ChevronRightRoundedIcon from "@mui/icons-material/ChevronRightRounded";
import PermMediaRoundedIcon from "@mui/icons-material/PermMediaRounded";
import PlayArrowRoundedIcon from "@mui/icons-material/PlayArrowRounded";
import PhotoRoundedIcon from "@mui/icons-material/PhotoRounded";
import { useRef, useState } from "react";

import { TYPOGRAPHY } from "../../../theme/typography";

function MediaTypeBadge({ isVideo, isImage, mediaType }) {
  return (
    <Box
      sx={{
        position: "absolute",
        top: 10,
        left: 10,
        display: "flex",
        alignItems: "center",
        gap: 0.4,
        px: 0.9,
        py: 0.35,
        borderRadius: 1,
        bgcolor: "rgba(15, 23, 42, 0.68)",
        backdropFilter: "blur(2px)",
        pointerEvents: "none",
      }}
    >
      {isVideo ? (
        <PlayArrowRoundedIcon sx={{ fontSize: 13, color: "#fff" }} />
      ) : (
        <PhotoRoundedIcon sx={{ fontSize: 12, color: "#fff" }} />
      )}

      <Typography
        sx={{
          fontSize: 10.5,
          fontWeight: 700,
          color: "#fff",
          letterSpacing: "0.02em",
        }}
      >
        {isVideo ? "VIDEO" : isImage ? "PHOTO" : mediaType || "FILE"}
      </Typography>
    </Box>
  );
}

function MediaFrame({
  item,
  aspectRatio,
  rounded = 2.5,
  badge = true,
  hoverZoom = true,
}) {
  const mediaType = item.type?.toUpperCase();
  const isImage = mediaType === "IMAGE" || mediaType === "PHOTO";
  const isVideo = mediaType === "VIDEO";

  return (
    <Box
      sx={{
        position: "relative",
        width: "100%",
        height: aspectRatio === "16 / 10" ? "clamp(180px, 32vh, 280px)" : 88,
        overflow: "hidden",
        borderRadius: rounded,
        bgcolor: "action.hover",
        border: "1px solid",
        borderColor: "divider",
        flexShrink: 0,
        ...(hoverZoom && {
          "&:hover img": {
            transform: "scale(1.05)",
          },
        }),
      }}
    >
      {isImage && (
        <Box
          component="img"
          src={item.url}
          alt=""
          loading="lazy"
          sx={{
            width: "100%",
            height: "100%",
            display: "block",
            objectFit: "contain",
            transition: "transform 260ms ease",
          }}
        />
      )}

      {isVideo && (
        <Box
          component="video"
          src={item.url}
          controls
          preload="metadata"
          sx={{
            width: "100%",
            height: "100%",
            display: "block",
            objectFit: "contain",
          }}
        />
      )}

      {!isImage && !isVideo && (
        <Stack
          alignItems="center"
          justifyContent="center"
          spacing={0.5}
          sx={{ width: "100%", height: "100%" }}
        >
          <PermMediaRoundedIcon sx={{ fontSize: 24, color: "text.disabled" }} />
          <Typography
            sx={{
              ...TYPOGRAPHY.caption,
              color: "text.secondary",
              fontSize: 10,
            }}
          >
            {mediaType || "Media"}
          </Typography>
        </Stack>
      )}

      {badge && (isImage || isVideo) && (
        <MediaTypeBadge
          isVideo={isVideo}
          isImage={isImage}
          mediaType={mediaType}
        />
      )}
    </Box>
  );
}

export default function CalendarEventMedia({ event }) {
  const media = Array.isArray(event?.media)
    ? event.media.filter((item) => item?.url)
    : [];
  const [selection, setSelection] = useState({ mediaKey: "", index: 0 });
  const touchStartX = useRef(null);
  const mediaKey = media.map((item) => item.id || item.url).join("|");
  const activeIndex = selection.mediaKey === mediaKey ? selection.index : 0;

  if (!media.length) {
    return null;
  }

  const hasMultiple = media.length > 1;
  const currentIndex = Math.min(activeIndex, media.length - 1);
  const activeMedia = media[currentIndex];

  function showMedia(index) {
    setSelection({
      mediaKey,
      index: (index + media.length) % media.length,
    });
  }

  function handleTouchStart(event) {
    touchStartX.current = event.touches?.[0]?.clientX ?? null;
  }

  function handleTouchEnd(event) {
    if (touchStartX.current === null) {
      return;
    }

    const delta = (event.changedTouches?.[0]?.clientX ?? touchStartX.current) - touchStartX.current;
    touchStartX.current = null;

    if (!hasMultiple || Math.abs(delta) < 40 || event.target?.tagName === "VIDEO") {
      return;
    }

    showMedia(currentIndex + (delta < 0 ? 1 : -1));
  }

  function handleKeyDown(event) {
    if (!hasMultiple) {
      return;
    }
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      showMedia(currentIndex - 1);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      showMedia(currentIndex + 1);
    }
  }

  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,
        mt: 2.5,
        pt: 2.5,
        borderTop: "1px solid",
        borderColor: "divider",
      }}
    >
      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1.5 }}>
        <PermMediaRoundedIcon sx={{ fontSize: 18, color: "text.secondary" }} />

        <Typography
          component="h3"
          sx={{
            ...TYPOGRAPHY.cardTitle,
            color: "text.primary",
          }}
        >
          Media
        </Typography>

        <Box
          sx={{
            px: 0.85,
            py: 0.1,
            borderRadius: 5,
            bgcolor: "action.hover",
          }}
        >
          <Typography
            sx={{
              ...TYPOGRAPHY.caption,
              color: "text.secondary",
              fontWeight: 700,
              fontSize: 10.5,
            }}
          >
            {media.length}
          </Typography>
        </Box>
      </Stack>

      <Box
        role={hasMultiple ? "group" : undefined}
        aria-label={hasMultiple ? "Post media carousel" : undefined}
        tabIndex={hasMultiple ? 0 : undefined}
        onKeyDown={handleKeyDown}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        sx={{ width: "100%", minWidth: 0, touchAction: "pan-y" }}
      >
        <MediaFrame
          key={activeMedia.id || activeMedia.url}
          item={activeMedia}
          aspectRatio="16 / 10"
          rounded={2.5}
          hoverZoom={!hasMultiple}
        />

        {hasMultiple && (
          <Stack
            direction="row"
            alignItems="center"
            justifyContent="space-between"
            sx={{ mt: 0.75, minWidth: 0 }}
          >
            <IconButton
              aria-label="Previous media"
              onClick={() => showMedia(currentIndex - 1)}
              size="small"
              sx={{ border: "1px solid", borderColor: "divider" }}
            >
              <ChevronLeftRoundedIcon />
            </IconButton>
            <Typography
              aria-live="polite"
              sx={{ ...TYPOGRAPHY.caption, color: "text.secondary", fontWeight: 700 }}
            >
              {currentIndex + 1} / {media.length}
            </Typography>
            <IconButton
              aria-label="Next media"
              onClick={() => showMedia(currentIndex + 1)}
              size="small"
              sx={{ border: "1px solid", borderColor: "divider" }}
            >
              <ChevronRightRoundedIcon />
            </IconButton>
          </Stack>
        )}
      </Box>
    </Box>
  );
}
