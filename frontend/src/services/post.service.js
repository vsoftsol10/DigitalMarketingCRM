import api from "../api/axios";

import { CREATE_POST } from "../data/post";

class PostService {
  // ============================================================
  // CREATE POST PAGE CONFIGURATION
  // ============================================================
  //
  // Platform and media capabilities are static frontend configuration.
  // Organizations and connected accounts are loaded by the page from their
  // existing APIs because they are organization-specific runtime data.
  //

  async getCreatePostData() {
    return CREATE_POST;
  }

  // ============================================================
  // CREATE POST
  // ============================================================
  //
  async createPost(organizationId, payload) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    if (!payload) {
      throw new Error("Create post payload is required.");
    }

    const formData = new FormData();

    payload.targets.forEach((target, index) => {
      formData.append(`targets[${index}]social_account`, target.social_account);
      formData.append(`targets[${index}]content_type`, target.content_type);
    });

    formData.append("caption", payload.caption);
    formData.append("publish_type", payload.publish_type);
    formData.append("timezone", payload.timezone);

    if (payload.publish_date) {
      formData.append("publish_date", payload.publish_date);
    }

    if (payload.publish_time) {
      formData.append("publish_time", payload.publish_time);
    }

    payload.media.forEach((media, index) => {
      formData.append(`media[${index}]file`, media.file);
      formData.append(`media[${index}]media_type`, media.media_type);
    });

    const response = await api.post(
      `/posts/organizations/${organizationId}/`,
      formData,
    );

    return response.data;
  }
}

export default new PostService();
