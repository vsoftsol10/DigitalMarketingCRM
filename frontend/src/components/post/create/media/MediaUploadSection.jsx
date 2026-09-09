import { Stack, Typography } from "@mui/material";

import { useFormContext } from "react-hook-form";

import SectionCard from "../SectionCard";

import MediaDropzone from "./MediaDropzone";
import MediaPreviewGrid from "./MediaPreviewGrid";

import useMediaUpload from "../../../../hooks/post/useMediaUpload";

import { TYPOGRAPHY } from "../../../../theme/typography";

export default function MediaUploadSection({ config }) {
  const {
    formState: { errors },
  } = useFormContext();

  const {
    media,

    inputRef,

    handleBrowse,

    handleInputChange,

    handleDrop,

    handleDragOver,

    removeMedia,

    clearMedia,
  } = useMediaUpload({
    config,
  });

  const hasMedia = media.length > 0;

  return (
    <SectionCard
      title="Upload Media"
      description="Drag & drop or browse to upload images, video, or carousel."
      compact
    >
      <Stack
        spacing={2}
        sx={{
          // prevents a jarring layout jump before/after upload
          minHeight: { xs: 265, sm: 280 },
        }}
      >
        {/* =====================================================
            EMPTY STATE
        ===================================================== */}

        {!hasMedia && (
          <MediaDropzone
            config={config}
            onBrowse={handleBrowse}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
          />
        )}

        {/* =====================================================
            VALIDATION ERROR
        ===================================================== */}

        {errors.media && (
          <Typography
            sx={{
              ...TYPOGRAPHY.helperText,
              color: "error.main",
              mt: -0.5,
            }}
          >
            {errors.media.message}
          </Typography>
        )}

        {/* =====================================================
            UPLOADED MEDIA
        ===================================================== */}

        {hasMedia && <MediaPreviewGrid media={media} onRemove={removeMedia} />}

        {/* =====================================================
            ACTIONS AFTER UPLOAD
        ===================================================== */}

        {hasMedia && (
          <Stack
            direction="row"
            alignItems="center"
            spacing={1.5}
            sx={{
              pt: 0.25,
            }}
          >
            <button
              type="button"
              // onClick={handleBrowse}
              onClick={() => handleBrowse("ALL")}
              style={{
                height: 40,
                padding: "0 18px",
                border: "1px solid #D4DCE8",
                borderRadius: "10px",
                background: "#FFFFFF",
                color: "#4D576A",
                fontFamily: "inherit",
                fontSize: "13px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Add More
            </button>

            <button
              type="button"
              onClick={clearMedia}
              style={{
                height: 40,
                padding: "0 12px",
                border: "none",
                borderRadius: "10px",
                background: "transparent",
                color: "#5D687B",
                fontFamily: "inherit",
                fontSize: "13px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Clear All
            </button>
          </Stack>
        )}
      </Stack>

      {/* =====================================================
          HIDDEN FILE INPUT
          IMPORTANT: this is now always mounted here (not inside
          MediaDropzone), so it survives even after hasMedia
          becomes true. This is what makes "Add More" work.
      ===================================================== */}

      <input
        hidden
        ref={inputRef}
        type="file"
        multiple={Boolean(config?.allow_multiple)}
        accept={config?.accepted_types?.join(",") || ""}
        onChange={handleInputChange}
      />
    </SectionCard>
  );
}
