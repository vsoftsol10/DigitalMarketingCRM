// import { useRef } from "react";

// import { useFormContext } from "react-hook-form";

// import {
//   createMediaObject,
//   getFileKey,
//   revokePreviewUrl,
//   validateFileSize,
//   validateFileType,
// } from "../../utils/post/media.utils";

// export default function useMediaUpload({ config }) {
//   const inputRef = useRef(null);

//   const { watch, setValue } = useFormContext();

//   const media = watch("media") || [];

//   function handleBrowse() {
//     inputRef.current?.click();
//   }

//   function appendFiles(files) {
//     const selectedFiles = Array.from(files || []);

//     if (!selectedFiles.length) {
//       return;
//     }

//     const existingKeys = new Set(media.map((item) => getFileKey(item.file)));

//     const newMedia = [];
//     const rejectedFiles = [];

//     for (const file of selectedFiles) {
//       const fileKey = getFileKey(file);

//       // Duplicate protection
//       if (existingKeys.has(fileKey)) {
//         rejectedFiles.push({
//           file,
//           reason: "DUPLICATE",
//         });

//         continue;
//       }

//       // Maximum file count
//       if (media.length + newMedia.length >= config.max_files) {
//         rejectedFiles.push({
//           file,
//           reason: "MAX_FILES",
//         });

//         continue;
//       }

//       // File type validation
//       if (!validateFileType(file, config.accepted_types)) {
//         rejectedFiles.push({
//           file,
//           reason: "INVALID_TYPE",
//         });

//         continue;
//       }

//       // File size validation
//       if (!validateFileSize(file, config.max_file_size_mb)) {
//         rejectedFiles.push({
//           file,
//           reason: "FILE_TOO_LARGE",
//         });

//         continue;
//       }

//       newMedia.push(
//         createMediaObject({
//           file,
//         }),
//       );

//       existingKeys.add(fileKey);
//     }

//     if (newMedia.length) {
//       setValue("media", [...media, ...newMedia], {
//         shouldDirty: true,
//         shouldValidate: true,
//       });
//     }

//     return rejectedFiles;
//   }

//   function handleInputChange(event) {
//     appendFiles(event.target.files);

//     event.target.value = "";
//   }

//   function handleDrop(event) {
//     event.preventDefault();

//     appendFiles(event.dataTransfer.files);
//   }

//   function handleDragOver(event) {
//     event.preventDefault();

//     if (event.dataTransfer) {
//       event.dataTransfer.dropEffect = "copy";
//     }
//   }

//   function removeMedia(id) {
//     const target = media.find((item) => item.id === id);

//     if (target) {
//       revokePreviewUrl(target);
//     }

//     setValue(
//       "media",
//       media.filter((item) => item.id !== id),
//       {
//         shouldDirty: true,
//         shouldValidate: true,
//       },
//     );
//   }

//   function clearMedia() {
//     media.forEach(revokePreviewUrl);

//     setValue("media", [], {
//       shouldDirty: true,
//       shouldValidate: true,
//     });
//   }

//   // Cleanup local blob URLs
//   // when component unmounts.

//   // useEffect(() => {
//   //   return () => {
//   //     media.forEach(
//   //       revokePreviewUrl,
//   //     );
//   //   };
//   // }, []);

//   return {
//     media,

//     inputRef,

//     handleBrowse,

//     handleInputChange,

//     handleDrop,

//     handleDragOver,

//     removeMedia,

//     clearMedia,

//     appendFiles,
//   };
// }

import { useCallback, useEffect, useRef, useState } from "react";

import { useFormContext } from "react-hook-form";

import {
  createMediaObject,
  readImageDimensions,
  revokePreviewUrl,
  validateMediaFiles,
} from "../../utils/post/media.utils";
import postMediaUploadService from "../../services/postMediaUpload.service";

const IMAGE_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
];

const VIDEO_TYPES = [
  "video/mp4",
  "video/quicktime",
];
const EMPTY_MEDIA = [];

export default function useMediaUpload({
  config,
  organizationId,
  uploadPolicy,
  onClearMediaReady,
}) {
  const inputRef = useRef(null);

  const uploadModeRef = useRef("ALL");

  const { watch, setValue, getValues } =
    useFormContext();

  const [rejectedFiles, setRejectedFiles] = useState([]);
  const uploadRequestsRef = useRef(new Map());
  const abortControllersRef = useRef(new Map());

  const watchedMedia = watch("media");
  const media = Array.isArray(watchedMedia) ? watchedMedia : EMPTY_MEDIA;

  const updateMediaItem = useCallback((id, patch) => {
    const currentMedia = getValues("media") || [];
    setValue(
      "media",
      currentMedia.map((item) => (
        item.id === id ? { ...item, ...patch } : item
      )),
      { shouldDirty: true, shouldValidate: true },
    );
  }, [getValues, setValue]);

  const loadImageDimensions = useCallback((mediaItem) => {
    if (mediaItem.type !== "IMAGE") {
      return;
    }

    readImageDimensions(mediaItem.file)
      .then(({ width, height }) => {
        updateMediaItem(mediaItem.id, {
          width,
          height,
          dimensionsPending: false,
          dimensionsError: null,
        });
      })
      .catch((error) => {
        updateMediaItem(mediaItem.id, {
          dimensionsPending: false,
          dimensionsError: error?.message || "Unable to read image dimensions.",
        });
      });
  }, [updateMediaItem]);

  const startUpload = useCallback(async (mediaItem) => {
    if (!organizationId || uploadRequestsRef.current.has(mediaItem.id)) {
      return;
    }

    const controller = new AbortController();
    uploadRequestsRef.current.set(mediaItem.id, true);
    abortControllersRef.current.set(mediaItem.id, controller);

    try {
      updateMediaItem(mediaItem.id, {
        status: "UPLOADING",
        progress: 0,
        uploadError: "",
      });
      const session = await postMediaUploadService.createSession(
        organizationId,
        mediaItem.file,
      );
      updateMediaItem(mediaItem.id, {
        uploadSessionId: session.session_id,
        status: "UPLOADING",
      });

      const uploadResponse = await postMediaUploadService.uploadToCloudinary(
        session,
        mediaItem.file,
        {
          signal: controller.signal,
          refreshSession: () => postMediaUploadService.getSession(
            organizationId,
            session.session_id,
          ),
          onProgress: (uploaded, total) => {
            const progress = total > 0
              ? Math.min(100, Math.max(0, Math.round((uploaded / total) * 100)))
              : 0;
            updateMediaItem(mediaItem.id, {
              status: "UPLOADING",
              progress,
            });
          },
        },
      );
      const finalized = await postMediaUploadService.finalizeSession(
        organizationId,
        session.session_id,
        uploadResponse,
      );
      updateMediaItem(mediaItem.id, {
        uploadSessionId: finalized.media_asset_id || session.session_id,
        status: "UPLOADED",
        progress: 100,
        uploadError: "",
      });
    } catch (error) {
      if (error?.name === "AbortError") {
        // Return an interrupted item to LOCAL so a development StrictMode
        // remount or an explicit retry can safely start a fresh session.
        updateMediaItem(mediaItem.id, {
          status: "LOCAL",
          uploadError: "",
          progress: 0,
        });
        return;
      }
      updateMediaItem(mediaItem.id, {
        status: "FAILED",
        uploadError: error?.message || "Media upload failed. Try again.",
      });
    } finally {
      uploadRequestsRef.current.delete(mediaItem.id);
      abortControllersRef.current.delete(mediaItem.id);
    }
  }, [organizationId, updateMediaItem]);

  useEffect(() => {
    if (!organizationId) {
      return;
    }
    media
      .filter((item) => item.status === "LOCAL")
      .forEach((item) => startUpload(item));
  }, [media, organizationId, startUpload]);

  useEffect(() => () => {
    abortControllersRef.current.forEach((controller) => controller.abort());
  }, []);

  // ============================================================
  // BROWSE
  // ============================================================

  function handleBrowse(mode = "ALL") {
    const input = inputRef.current;

    if (!input) {
      return;
    }

    uploadModeRef.current = mode;

    // ==========================================================
    // IMAGE
    // ==========================================================

    if (mode === "IMAGE") {
      input.accept =
        IMAGE_TYPES.join(",");

      input.multiple = false;
    }

    // ==========================================================
    // VIDEO
    // ==========================================================

    else if (mode === "VIDEO") {
      input.accept =
        VIDEO_TYPES.join(",");

      input.multiple = false;
    }

    // ==========================================================
    // CAROUSEL
    // ==========================================================

    else if (mode === "CAROUSEL") {
      input.accept =
        config.accepted_types.join(",");

      input.multiple = true;
    }

    // ==========================================================
    // ALL / ADD MORE
    // ==========================================================

    else {
      input.accept =
        config.accepted_types.join(",");

      input.multiple =
        Boolean(
          config.allow_multiple,
        );
    }

    input.click();
  }

  // ============================================================
  // APPEND FILES
  // ============================================================

  function appendFiles(files) {
    const selectedFiles =
      Array.from(files || []);

    if (!selectedFiles.length) {
      return [];
    }

    const mode =
      uploadModeRef.current;

    let allowedTypes =
      config.accepted_types;

    // ==========================================================
    // MODE VALIDATION
    // ==========================================================

    if (mode === "IMAGE") {
      allowedTypes = IMAGE_TYPES;
    }

    if (mode === "VIDEO") {
      allowedTypes = VIDEO_TYPES;
    }

    // CAROUSEL + ALL already use config.accepted_types.

    const { accepted, rejected: rejectedFiles } = validateMediaFiles({
      files: selectedFiles,
      existingMedia: media,
      maxFiles: config.max_files,
      acceptedTypes: allowedTypes,
      uploadPolicy,
    });
    const newMedia = accepted.map((file) => {
      const mediaObject = createMediaObject({ file });
      loadImageDimensions(mediaObject);
      return mediaObject;
    });

    // ==========================================================
    // UPDATE FORM
    // ==========================================================

    if (newMedia.length) {
      setValue(
        "media",
        [
          ...media,
          ...newMedia,
        ],
        {
          shouldDirty: true,
          shouldValidate: true,
        },
      );
    }

    setRejectedFiles(rejectedFiles);

    return rejectedFiles;
  }

  // ============================================================
  // FILE INPUT CHANGE
  // ============================================================

  function handleInputChange(
    event,
  ) {
    const files =
      event.target.files;

    const rejectedFiles =
      appendFiles(files);

    /*
     * Reset the native file input.
     *
     * This is important because the user should
     * be able to select the same file again after
     * removing it.
     */

    event.target.value = "";

    return rejectedFiles;
  }

  // ============================================================
  // DRAG & DROP
  // ============================================================

  function handleDrop(event) {
    event.preventDefault();

    /*
     * Drag/drop is treated as generic media upload.
     * Platform/content compatibility is handled separately.
     */

    uploadModeRef.current = "ALL";

    return appendFiles(
      event.dataTransfer?.files,
    );
  }

  // ============================================================
  // DRAG OVER
  // ============================================================

  function handleDragOver(event) {
    event.preventDefault();

    if (event.dataTransfer) {
      event.dataTransfer.dropEffect =
        "copy";
    }
  }

  // ============================================================
  // REMOVE MEDIA
  // ============================================================

  function removeMedia(id) {
    const target =
      media.find(
        (item) => item.id === id,
      );

    if (target) {
      abortControllersRef.current.get(id)?.abort();
      abortControllersRef.current.delete(id);
      uploadRequestsRef.current.delete(id);
      revokePreviewUrl(target);
    }

    setValue(
      "media",
      media.filter(
        (item) => item.id !== id,
      ),
      {
        shouldDirty: true,
        shouldValidate: true,
      },
    );
  }

  // ============================================================
  // CLEAR ALL
  // ============================================================

  const clearMedia = useCallback(() => {
    abortControllersRef.current.forEach((controller) => controller.abort());
    abortControllersRef.current.clear();
    uploadRequestsRef.current.clear();
    media.forEach(
      revokePreviewUrl,
    );

    setValue(
      "media",
      [],
      {
        shouldDirty: true,
        shouldValidate: true,
      },
    );
  }, [media, setValue]);

  useEffect(() => {
    onClearMediaReady?.(clearMedia);

    return () => {
      onClearMediaReady?.(null);
    };
  }, [clearMedia, onClearMediaReady]);

  // ============================================================
  // RETURN
  // ============================================================

  return {
    media,
    rejectedFiles,

    inputRef,

    handleBrowse,

    handleInputChange,

    handleDrop,

    handleDragOver,

    removeMedia,

    clearMedia,

    appendFiles,
    retryUpload: (id) => {
      const target = (getValues("media") || []).find((item) => item.id === id);
      if (!target) return;
      updateMediaItem(id, { status: "LOCAL", uploadError: "", progress: 0 });
      startUpload({ ...target, status: "LOCAL", uploadError: "", progress: 0 });
    },
  };
}
