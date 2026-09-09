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

import { useRef } from "react";

import { useFormContext } from "react-hook-form";

import {
  createMediaObject,
  getFileKey,
  revokePreviewUrl,
  validateFileSize,
  validateFileType,
} from "../../utils/post/media.utils";

const IMAGE_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
];

const VIDEO_TYPES = [
  "video/mp4",
];

export default function useMediaUpload({
  config,
}) {
  const inputRef = useRef(null);

  const uploadModeRef = useRef("ALL");

  const { watch, setValue } =
    useFormContext();

  const media =
    watch("media") || [];

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

    // ==========================================================
    // DUPLICATE LOOKUP
    // ==========================================================

    const existingKeys =
      new Set(
        media.map((item) =>
          getFileKey(item.file),
        ),
      );

    const newMedia = [];
    const rejectedFiles = [];

    // ==========================================================
    // PROCESS FILES
    // ==========================================================

    for (const file of selectedFiles) {
      const fileKey =
        getFileKey(file);

      // --------------------------------------------------------
      // DUPLICATE
      // --------------------------------------------------------

      if (
        existingKeys.has(fileKey)
      ) {
        rejectedFiles.push({
          file,
          reason: "DUPLICATE",
        });

        continue;
      }

      // --------------------------------------------------------
      // MAX FILE COUNT
      // --------------------------------------------------------

      if (
        media.length +
          newMedia.length >=
        config.max_files
      ) {
        rejectedFiles.push({
          file,
          reason: "MAX_FILES",
        });

        continue;
      }

      // --------------------------------------------------------
      // FILE TYPE
      // --------------------------------------------------------

      if (
        !validateFileType(
          file,
          allowedTypes,
        )
      ) {
        rejectedFiles.push({
          file,
          reason: "INVALID_TYPE",
        });

        continue;
      }

      // --------------------------------------------------------
      // FILE SIZE
      // --------------------------------------------------------

      if (
        !validateFileSize(
          file,
          config.max_file_size_mb,
        )
      ) {
        rejectedFiles.push({
          file,
          reason: "FILE_TOO_LARGE",
        });

        continue;
      }

      // --------------------------------------------------------
      // CREATE MEDIA OBJECT
      // --------------------------------------------------------

      const mediaObject =
        createMediaObject({
          file,
        });

      newMedia.push(
        mediaObject,
      );

      existingKeys.add(
        fileKey,
      );
    }

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

  function clearMedia() {
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
  }

  // ============================================================
  // RETURN
  // ============================================================

  return {
    media,

    inputRef,

    handleBrowse,

    handleInputChange,

    handleDrop,

    handleDragOver,

    removeMedia,

    clearMedia,

    appendFiles,
  };
}