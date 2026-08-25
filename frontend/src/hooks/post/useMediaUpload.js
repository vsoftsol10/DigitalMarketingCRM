// import { useRef } from "react";
// import { useFormContext } from "react-hook-form";

// import {
//   createMediaObject,
//   validateFileSize,
//   validateFileType,
// } from "../../utils/post/media.utils";

// export default function useMediaUpload({
//   config,
// }) {
//   const inputRef = useRef(null);

//   const { watch, setValue } =
//     useFormContext();

//   const media = watch("media") || [];

//   function handleBrowse() {
//     inputRef.current?.click();
//   }

//   function appendFiles(files) {
//     const uploadedMedia = [];

//     Array.from(files).forEach((file) => {
//       if (
//         !validateFileType(
//           file,
//           config.accepted_types,
//         )
//       ) {
//         return;
//       }

//       if (
//         !validateFileSize(
//           file,
//           config.max_file_size_mb,
//         )
//       ) {
//         return;
//       }

//       uploadedMedia.push(
//         createMediaObject({
//           file,
//         }),
//       );
//     });

//     setValue(
//       "media",
//       [...media, ...uploadedMedia],
//       {
//         shouldDirty: true,
//         shouldValidate: true,
//       },
//     );
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
//   }

//   function removeMedia(id) {
//     setValue(
//       "media",
//       media.filter(
//         (item) => item.id !== id,
//       ),
//       {
//         shouldDirty: true,
//       },
//     );
//   }

//   function clearMedia() {
//     setValue("media", []);
//   }

//   return {
//     media,

//     inputRef,

//     handleBrowse,

//     handleInputChange,

//     handleDrop,

//     handleDragOver,

//     removeMedia,

//     clearMedia,
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

export default function useMediaUpload({ config }) {
  const inputRef = useRef(null);

  const { watch, setValue } = useFormContext();

  const media = watch("media") || [];

  function handleBrowse() {
    inputRef.current?.click();
  }

  function appendFiles(files) {
    const selectedFiles = Array.from(files || []);

    if (!selectedFiles.length) {
      return;
    }

    const existingKeys = new Set(media.map((item) => getFileKey(item.file)));

    const newMedia = [];
    const rejectedFiles = [];

    for (const file of selectedFiles) {
      const fileKey = getFileKey(file);

      // Duplicate protection
      if (existingKeys.has(fileKey)) {
        rejectedFiles.push({
          file,
          reason: "DUPLICATE",
        });

        continue;
      }

      // Maximum file count
      if (media.length + newMedia.length >= config.max_files) {
        rejectedFiles.push({
          file,
          reason: "MAX_FILES",
        });

        continue;
      }

      // File type validation
      if (!validateFileType(file, config.accepted_types)) {
        rejectedFiles.push({
          file,
          reason: "INVALID_TYPE",
        });

        continue;
      }

      // File size validation
      if (!validateFileSize(file, config.max_file_size_mb)) {
        rejectedFiles.push({
          file,
          reason: "FILE_TOO_LARGE",
        });

        continue;
      }

      newMedia.push(
        createMediaObject({
          file,
        }),
      );

      existingKeys.add(fileKey);
    }

    if (newMedia.length) {
      setValue("media", [...media, ...newMedia], {
        shouldDirty: true,
        shouldValidate: true,
      });
    }

    return rejectedFiles;
  }

  function handleInputChange(event) {
    appendFiles(event.target.files);

    event.target.value = "";
  }

  function handleDrop(event) {
    event.preventDefault();

    appendFiles(event.dataTransfer.files);
  }

  function handleDragOver(event) {
    event.preventDefault();

    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = "copy";
    }
  }

  function removeMedia(id) {
    const target = media.find((item) => item.id === id);

    if (target) {
      revokePreviewUrl(target);
    }

    setValue(
      "media",
      media.filter((item) => item.id !== id),
      {
        shouldDirty: true,
        shouldValidate: true,
      },
    );
  }

  function clearMedia() {
    media.forEach(revokePreviewUrl);

    setValue("media", [], {
      shouldDirty: true,
      shouldValidate: true,
    });
  }

  // Cleanup local blob URLs
  // when component unmounts.

  // useEffect(() => {
  //   return () => {
  //     media.forEach(
  //       revokePreviewUrl,
  //     );
  //   };
  // }, []);

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
