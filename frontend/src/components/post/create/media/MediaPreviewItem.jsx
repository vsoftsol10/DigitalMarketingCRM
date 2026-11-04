import { Box, Button, IconButton, LinearProgress, Typography } from "@mui/material";

import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import PlayArrowRoundedIcon from "@mui/icons-material/PlayArrowRounded";
import ImageOutlinedIcon from "@mui/icons-material/ImageOutlined";

export default function MediaPreviewItem({ media, index = 0, onRemove, onRetry }) {
  const isImage = media?.type === "IMAGE";

  const isVideo = media?.type === "VIDEO";

  return (
    <Box
      sx={{
        position: "relative",

        width: "100%",
        aspectRatio: "1 / 1",

        borderRadius: "14px",

        overflow: "hidden",

        bgcolor: "#E9EDF3",

        border: "1px solid",
        borderColor: "#DCE2EB",
      }}
    >
      {/* =====================================================
          MEDIA PREVIEW
      ===================================================== */}

      {isImage && media.preview ? (
        <Box
          component="img"
          src={media.preview}
          alt={media.name || `Media ${index + 1}`}
          sx={{
            width: "100%",
            height: "100%",

            display: "block",

            objectFit: "cover",
          }}
        />
      ) : isVideo && media.preview ? (
        <Box
          component="video"
          src={media.preview}
          muted
          playsInline
          preload="metadata"
          sx={{
            width: "100%",
            height: "100%",

            display: "block",

            objectFit: "cover",

            bgcolor: "#111827",
          }}
        />
      ) : (
        <Box
          sx={{
            width: "100%",
            height: "100%",

            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {isVideo ? (
            <PlayArrowRoundedIcon
              sx={{
                fontSize: 38,
                color: "#718096",
              }}
            />
          ) : (
            <ImageOutlinedIcon
              sx={{
                fontSize: 38,
                color: "#8795AC",
              }}
            />
          )}
        </Box>
      )}

      {/* =====================================================
          INDEX
      ===================================================== */}

      <Box
        sx={{
          position: "absolute",

          top: 9,
          left: 9,

          minWidth: 22,
          height: 22,

          px: 0.5,

          borderRadius: "6px",

          bgcolor: "rgba(51, 61, 78, 0.72)",

          color: "#FFFFFF",

          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Typography
          sx={{
            fontSize: 11,
            fontWeight: 600,
            lineHeight: 1,
          }}
        >
          {index + 1}
        </Typography>
      </Box>

      {media?.status && media.status !== "UPLOADED" && (
        <Box
          sx={{
            position: "absolute",
            left: 8,
            right: 8,
            bottom: 42,
            px: 1,
            py: 0.5,
            borderRadius: 1,
            bgcolor: "rgba(15, 23, 42, 0.78)",
          }}
        >
          <Typography sx={{ color: "#fff", fontSize: 10, mb: 0.35 }}>
            {media.status === "FAILED"
              ? media.uploadError || "Upload failed"
              : media.status === "UPLOADING"
                ? `Uploading ${media.progress || 0}%`
                : media.status === "PROCESSING"
                  ? "Processing"
                  : "Preparing upload"}
          </Typography>
          {media.status === "UPLOADING" && (
            <LinearProgress
              variant="determinate"
              value={media.progress || 0}
              sx={{ height: 3, borderRadius: 2 }}
            />
          )}
          {media.status === "FAILED" && (
            <Button
              size="small"
              onClick={() => onRetry?.(media.id)}
              sx={{
                minWidth: 0,
                p: 0,
                color: "#bfdbfe",
                fontSize: 10,
                textTransform: "none",
              }}
            >
              Retry upload
            </Button>
          )}
        </Box>
      )}

      {/* =====================================================
          REMOVE
      ===================================================== */}

      <IconButton
        size="small"
        aria-label={`Remove ${media?.name || `media ${index + 1}`}`}
        onClick={() => onRemove?.(media.id)}
        sx={{
          position: "absolute",

          top: 7,
          right: 7,

          width: 26,
          height: 26,

          bgcolor: "rgba(255,255,255,0.95)",

          color: "#475569",

          border: "1px solid rgba(203, 213, 225, 0.9)",

          "&:hover": {
            bgcolor: "#FFFFFF",
            color: "error.main",
          },
        }}
      >
        <CloseRoundedIcon
          sx={{
            fontSize: 15,
          }}
        />
      </IconButton>

      {/* =====================================================
          FILE NAME
      ===================================================== */}

      <Box
        sx={{
          position: "absolute",

          left: 8,
          right: 8,
          bottom: 8,

          px: 1,

          py: 0.55,

          borderRadius: "6px",

          bgcolor: "rgba(55, 63, 78, 0.72)",

          backdropFilter: "blur(3px)",
        }}
      >
        <Typography
          noWrap
          title={media?.name || ""}
          sx={{
            fontSize: 11,

            lineHeight: 1.3,

            color: "#FFFFFF",
          }}
        >
          {media?.name || `Media ${index + 1}`}
        </Typography>
      </Box>
    </Box>
  );
}
