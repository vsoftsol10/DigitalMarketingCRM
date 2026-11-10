// ==========================================
// MEDIA TYPES
// ==========================================

export const MEDIA_TYPE = {
  IMAGE: "IMAGE",
  VIDEO: "VIDEO",
};

// ==========================================
// MEDIA STATUS
// ==========================================

export const MEDIA_STATUS = {
  LOCAL: "LOCAL",
  UPLOADING: "UPLOADING",
  UPLOADED: "UPLOADED",
  FAILED: "FAILED",
};

// ==========================================
// FILE TYPE HELPERS
// ==========================================

export function isImage(file) {
  return file?.type?.startsWith("image/") ?? false;
}

export function isVideo(file) {
  return file?.type?.startsWith("video/") ?? false;
}

// ==========================================
// FILE VALIDATION
// ==========================================

export function validateFileType(file, acceptedTypes = []) {
  if (!file || !acceptedTypes.length) {
    return true;
  }

  return acceptedTypes.includes(file.type);
}

export function validateFileSize(file, maxFileSizeMB) {
  if (!file || !maxFileSizeMB) {
    return true;
  }

  const maxBytes = maxFileSizeMB * 1024 * 1024;

  return file.size <= maxBytes;
}

export function validateFileSizeBytes(file, maxFileSizeBytes) {
  return Boolean(
    file
    && Number.isSafeInteger(maxFileSizeBytes)
    && maxFileSizeBytes > 0
    && file.size <= maxFileSizeBytes,
  );
}

export function validateMediaFiles({
  files = [],
  existingMedia = [],
  maxFiles,
  acceptedTypes = [],
  uploadPolicy,
}) {
  const existingKeys = new Set(
    existingMedia.map((item) => getFileKey(item?.file)),
  );
  const accepted = [];
  const rejected = [];

  for (const file of Array.from(files || [])) {
    const fileKey = getFileKey(file);
    let reason = "";

    if (existingKeys.has(fileKey)) {
      reason = "DUPLICATE";
    } else if (existingMedia.length + accepted.length >= maxFiles) {
      reason = "MAX_FILES";
    } else if (!validateFileType(file, acceptedTypes)) {
      reason = "INVALID_TYPE";
    } else {
      const maxBytes = file.type?.startsWith("image/")
        ? uploadPolicy?.image_max_size_bytes
        : file.type?.startsWith("video/")
          ? uploadPolicy?.video_max_size_bytes
          : null;

      if (!Number.isSafeInteger(maxBytes) || maxBytes <= 0) {
        reason = "POLICY_UNAVAILABLE";
      } else if (!validateFileSizeBytes(file, maxBytes)) {
        reason = "FILE_TOO_LARGE";
      }
    }

    if (reason) {
      rejected.push({ file, reason });
      continue;
    }

    accepted.push(file);
    existingKeys.add(fileKey);
  }

  return { accepted, rejected };
}

// ==========================================
// FILE SIZE FORMATTER
// ==========================================

export function formatFileSize(bytes = 0) {
  if (bytes === 0) {
    return "0 Bytes";
  }

  const units = ["Bytes", "KB", "MB", "GB"];

  const index = Math.floor(Math.log(bytes) / Math.log(1024));

  const safeIndex = Math.min(index, units.length - 1);

  return `${(bytes / Math.pow(1024, safeIndex)).toFixed(
    safeIndex === 0 ? 0 : 1,
  )} ${units[safeIndex]}`;
}

// ==========================================
// DUPLICATE FILE KEY
// ==========================================

export function getFileKey(file) {
  return [file?.name, file?.size, file?.type, file?.lastModified].join("|");
}

// ==========================================
// PREVIEW URL
// ==========================================

export function createPreviewUrl(file) {
  return URL.createObjectURL(file);
}

export function readImageDimensions(file) {
  return new Promise((resolve, reject) => {
    if (typeof Image === "undefined") {
      reject(new Error("Image dimensions are unavailable in this environment."));
      return;
    }

    const objectUrl = URL.createObjectURL(file);
    const image = new Image();

    image.onload = () => {
      URL.revokeObjectURL(objectUrl);
      resolve({
        width: image.naturalWidth,
        height: image.naturalHeight,
      });
    };

    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Unable to read image dimensions."));
    };

    image.src = objectUrl;
  });
}

// ==========================================
// MEDIA OBJECT
// ==========================================

export function createMediaObject({ file }) {
  const type = isImage(file) ? MEDIA_TYPE.IMAGE : MEDIA_TYPE.VIDEO;

  return {
    id: crypto.randomUUID(),

    file,

    preview: createPreviewUrl(file),

    name: file.name,

    mime_type: file.type,

    size: file.size,

    type,

    width: null,

    height: null,

    dimensionsPending: type === MEDIA_TYPE.IMAGE,

    dimensionsError: null,

    status: MEDIA_STATUS.LOCAL,

    progress: 0,

    error: null,

    // Server-side fields.
    // These will be populated after upload.
    media_id: null,

    uploadSessionId: null,
    uploadError: "",

    url: null,
  };
}

// ==========================================
// CLEANUP
// ==========================================

export function revokePreviewUrl(media) {
  if (media?.preview && media.preview.startsWith("blob:")) {
    URL.revokeObjectURL(media.preview);
  }
}
