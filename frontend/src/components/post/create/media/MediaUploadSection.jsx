import { Button, Stack, Typography } from "@mui/material";

import { useFormContext } from "react-hook-form";

import SectionCard from "../SectionCard";

import MediaDropzone from "./MediaDropzone";
import MediaPreviewGrid from "./MediaPreviewGrid";

import useMediaUpload from "../../../../hooks/post/useMediaUpload";

import { TYPOGRAPHY } from "../../../../theme/typography";
import { postDangerButtonSx, postSecondaryButtonSx } from "../postUiSx";

export default function MediaUploadSection({
  config,
  organizationId,
  uploadPolicy,
  onClearMediaReady,
}) {
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
    rejectedFiles,
    retryUpload,
  } = useMediaUpload({
    config,
    organizationId,
    uploadPolicy,
    onClearMediaReady,
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

        {rejectedFiles.length > 0 && (
          <Typography
            sx={{
              ...TYPOGRAPHY.helperText,
              color: "error.main",
              mt: -0.5,
            }}
          >
            {rejectedFiles.map(({ file, reason }) => (
              `${file?.name || "File"}: ${reason === "FILE_TOO_LARGE"
                ? "This file exceeds the configured upload limit."
                : reason === "INVALID_TYPE"
                  ? "This file format is not supported."
                  : reason === "MAX_FILES"
                    ? "The maximum number of files has been reached."
                    : reason === "POLICY_UNAVAILABLE"
                      ? "Upload limits could not be loaded. Reload the page before uploading."
                      : "This file was already selected."
              }`
            )).join(" ")}
          </Typography>
        )}

        {/* =====================================================
            UPLOADED MEDIA
        ===================================================== */}

        {hasMedia && (
          <MediaPreviewGrid
            media={media}
            organizationId={organizationId}
            onRemove={removeMedia}
            onRetry={retryUpload}
          />
        )}

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
            <Button
              type="button"
              onClick={() => handleBrowse("ALL")}
              variant="outlined"
              sx={{ ...postSecondaryButtonSx, px: 2.25, fontSize: 13, minHeight: 40 }}
            >
              Add More
            </Button>

            <Button
              type="button"
              onClick={clearMedia}
              variant="outlined"
              sx={{ ...postDangerButtonSx, px: 1.75, fontSize: 13, minHeight: 40 }}
            >
              Clear All
            </Button>
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
