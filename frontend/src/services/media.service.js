import api from "../api/axios";

class MediaService {
  async uploadMedia(file) {
    if (!file) {
      throw new Error("Media file is required.");
    }

    const formData = new FormData();

    formData.append("file", file);

    const response = await api.post("/media/upload/", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  }

  async deleteMedia(mediaId) {
    if (!mediaId) {
      throw new Error("Media ID is required.");
    }

    const response = await api.delete(`/media/${mediaId}/`);

    return response.data;
  }
}

export default new MediaService();
