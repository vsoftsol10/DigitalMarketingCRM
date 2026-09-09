import api from "../api/axios";

import { CREATE_POST } from "../data/post";

class PostService {
  // ============================================================
  // CREATE POST PAGE CONFIGURATION
  // ============================================================
  //
  // Current phase:
  // - Uses local configuration data.
  //
  // Later:
  // - This can be replaced with a backend configuration endpoint
  //   without changing the page/components.
  //

  async getCreatePostData() {
    return CREATE_POST;
  }

  // ============================================================
  // CREATE POST
  // ============================================================
  //
  // Backend endpoint is not implemented yet.
  //
  // Keep the API boundary ready, but do not silently fake
  // a successful response.
  //

  async createPost(payload) {
    if (!payload) {
      throw new Error("Create post payload is required.");
    }

    const response = await api.post("/posts/", payload);

    return response.data;
  }
}

export default new PostService();
