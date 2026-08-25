import { Box, Stack, Typography } from "@mui/material";

import PermMediaRoundedIcon from "@mui/icons-material/PermMediaRounded";
import PlayArrowRoundedIcon from "@mui/icons-material/PlayArrowRounded";
import PhotoRoundedIcon from "@mui/icons-material/PhotoRounded";

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
        aspectRatio,
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
            objectFit: "cover",
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
            objectFit: "cover",
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

  if (!media.length) {
    return null;
  }

  const [hero, ...rest] = media;
  const hasMultiple = media.length > 1;

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

      {/* ==========================================
          HERO — first asset, shown large
      ========================================== */}

      <MediaFrame item={hero} aspectRatio="16 / 10" rounded={2.5} />

      {/* ==========================================
          THUMBNAIL STRIP — remaining assets
      ========================================== */}

      {hasMultiple && (
        <Box
          sx={{
            display: "flex",
            gap: 1,
            mt: 1,
            overflowX: "auto",
            pb: 0.5,
            "&::-webkit-scrollbar": {
              height: 5,
            },
            "&::-webkit-scrollbar-thumb": {
              bgcolor: "divider",
              borderRadius: 10,
            },
            "&::-webkit-scrollbar-track": {
              bgcolor: "transparent",
            },
          }}
        >
          {rest.map((item) => (
            <Box key={item.id || item.url} sx={{ width: 88, flexShrink: 0 }}>
              <MediaFrame
                item={item}
                aspectRatio="1 / 1"
                rounded={1.75}
                badge={false}
              />
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
}
