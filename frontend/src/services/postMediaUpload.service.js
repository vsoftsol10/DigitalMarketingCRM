import api from "../api/axios";
import {
  getUploadChunkSize,
  shouldChunkUpload,
} from "../utils/post/uploadChunking.js";
const MEDIA_UPLOAD_FINALIZE_TIMEOUT = 120000;

const requireData = (response, fallbackMessage) => {
  if (!response?.data?.success) {
    throw new Error(response?.data?.message || fallbackMessage);
  }
  return response.data.data;
};

const sleep = (milliseconds) => (
  new Promise((resolve) => window.setTimeout(resolve, milliseconds))
);

function uploadRequest({
  session,
  file,
  start,
  end,
  uploadId,
  onProgress,
  signal,
}) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    let settled = false;
    const formData = new FormData();
    const isChunked = start !== 0 || end !== file.size;

    formData.append("file", file.slice(start, end), file.name);
    formData.append("api_key", session.api_key);
    formData.append("timestamp", String(session.timestamp));
    formData.append("signature", session.signature);
    formData.append("folder", session.folder);
    formData.append("public_id", session.public_id);
    formData.append("overwrite", session.overwrite || "false");

    const cleanup = () => {
      signal?.removeEventListener("abort", abort);
    };

    const resolveOnce = (value) => {
      if (settled) return;
      settled = true;
      cleanup();
      resolve(value);
    };

    const rejectOnce = (error) => {
      if (settled) return;
      settled = true;
      cleanup();
      reject(error);
    };

    const abort = () => {
      if (settled) return;
      xhr.abort();
      rejectOnce(new DOMException("Upload cancelled.", "AbortError"));
    };

    if (signal?.aborted) {
      abort();
      return;
    }

    signal?.addEventListener("abort", abort, { once: true });
    xhr.open("POST", session.upload_url);
    // Cloudinary returns JSON for both successful and failed upload requests.
    // Read it as text so the fallback parser remains usable even when a
    // response omits its JSON content type. Accessing responseText while an
    // XHR is in json mode can otherwise throw and leave the upload pending.
    xhr.responseType = "text";
    // Keep each request bounded while allowing slow client networks. Chunked
    // uploads retry a failed chunk without restarting the complete asset.
    xhr.timeout = 300000;

    if (isChunked) {
      xhr.setRequestHeader("X-Unique-Upload-Id", uploadId);
      xhr.setRequestHeader(
        "Content-Range",
        `bytes ${start}-${end - 1}/${file.size}`,
      );
    }

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress?.(
          Math.min(end, start + event.loaded),
          file.size,
        );
      }
    };

    xhr.onerror = () => rejectOnce(new Error("The media upload connection failed."));
    xhr.ontimeout = () => rejectOnce(new Error("The media upload timed out."));
    xhr.onload = () => {
      if (settled) return;
      let response = {};
      try {
        response = JSON.parse(xhr.responseText || "{}");
      } catch {
        // Keep the empty response object for non-JSON provider errors.
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress?.(end, file.size);
        resolveOnce(response);
        return;
      }

      const message = response?.error?.message
        || response?.message
        || `Cloudinary upload failed (${xhr.status}).`;
      rejectOnce(new Error(message));
    };

    xhr.send(formData);
  });
}

const postMediaUploadService = {
  async getUploadPolicy() {
    const response = await api.get("/posts/media-upload-policy/");
    return requireData(response, "Unable to load media upload limits.");
  },

  async createSession(organizationId, file) {
    const response = await api.post(
      `/posts/organizations/${organizationId}/media-upload-sessions/`,
      {
        filename: file.name,
        content_type: file.type,
        size: file.size,
      },
    );
    return requireData(response, "Unable to start the media upload.");
  },

  async uploadToCloudinary(
    session,
    file,
    { onProgress, signal, refreshSession } = {},
  ) {
    const shouldChunk = shouldChunkUpload(file.size, session.chunk_threshold);
    // Cloudinary requires every non-final chunk to be larger than 5 MB.
    // Keep deployments with a too-small/missing setting from producing an
    // invalid chunk sequence.
    const chunkSize = getUploadChunkSize(session.chunk_size);
    const uploadId = crypto.randomUUID();
    const maxAttempts = 3;
    let reportedBytes = 0;
    let activeSession = session;
    const reportProgress = (uploaded, total) => {
      const boundedUploaded = Math.min(
        total,
        Math.max(0, uploaded),
      );
      reportedBytes = Math.max(reportedBytes, boundedUploaded);
      onProgress?.(reportedBytes, total);
    };
    const refreshSignedSession = async () => {
      if (
        !refreshSession
        || (Date.now() / 1000) - Number(activeSession.timestamp || 0) < 45 * 60
      ) {
        return;
      }
      const refreshed = await refreshSession();
      if (refreshed?.upload) {
        activeSession = { ...activeSession, ...refreshed.upload };
      }
    };

    if (!shouldChunk) {
      return uploadRequest({
        session: activeSession,
        file,
        start: 0,
        end: file.size,
        uploadId,
        onProgress: reportProgress,
        signal,
      });
    }

    let offset = 0;
    let lastResponse = null;
    while (offset < file.size) {
      await refreshSignedSession();
      const end = Math.min(offset + chunkSize, file.size);
      let attempt = 0;
      while (attempt < maxAttempts) {
        try {
          lastResponse = await uploadRequest({
            session: activeSession,
            file,
            start: offset,
            end,
            uploadId,
            onProgress: reportProgress,
            signal,
          });
          break;
        } catch (error) {
          if (error?.name === "AbortError" || signal?.aborted) {
            throw error;
          }
          attempt += 1;
          if (attempt >= maxAttempts) {
            throw error;
          }
          await sleep(500 * (2 ** (attempt - 1)));
        }
      }
      offset = end;
    }

    return lastResponse;
  },

  async finalizeSession(organizationId, sessionId, uploadResponse) {
    const response = await api.post(
      `/posts/organizations/${organizationId}/media-upload-sessions/${sessionId}/`,
      {
        public_id: uploadResponse?.public_id,
        resource_type: uploadResponse?.resource_type,
        asset_id: uploadResponse?.asset_id || "",
      },
      { timeout: MEDIA_UPLOAD_FINALIZE_TIMEOUT },
    );
    return requireData(response, "Unable to verify the uploaded media.");
  },

  async getSession(organizationId, sessionId) {
    const response = await api.get(
      `/posts/organizations/${organizationId}/media-upload-sessions/${sessionId}/`,
    );
    return requireData(response, "Unable to check the media upload.");
  },
};

export default postMediaUploadService;
