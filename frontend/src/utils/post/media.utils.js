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

// ==========================================
// MEDIA OBJECT
// ==========================================

export function createMediaObject({ file }) {
  return {
    id: crypto.randomUUID(),

    file,

    preview: createPreviewUrl(file),

    name: file.name,

    mime_type: file.type,

    size: file.size,

    type: isImage(file) ? MEDIA_TYPE.IMAGE : MEDIA_TYPE.VIDEO,

    status: MEDIA_STATUS.LOCAL,

    progress: 0,

    error: null,

    // Server-side fields.
    // These will be populated after upload.
    media_id: null,

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
