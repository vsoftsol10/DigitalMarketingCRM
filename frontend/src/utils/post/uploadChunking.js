export const CLOUDINARY_MIN_CHUNK_SIZE = 6 * 1024 * 1024;

export const shouldChunkUpload = (fileSize, chunkThreshold) => (
  fileSize >= chunkThreshold
);

export const getUploadChunkSize = (configuredChunkSize) => Math.max(
  Number(configuredChunkSize) || 0,
  CLOUDINARY_MIN_CHUNK_SIZE,
);
