import api from "../api/axios";

import { CREATE_POST } from "../data/post";

class PostService {
  getPostPath(organizationId, postId) {
    if (!organizationId || !postId) {
      throw new Error("Organization and post IDs are required.");
    }

    return `/posts/organizations/${organizationId}/${postId}/`;
  }

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

  async schedulePost(organizationId, postId, payload) {
    const response = await api.post(
      `${this.getPostPath(organizationId, postId)}schedule/`,
      payload,
    );

    return response.data;
  }

  async schedulePostTarget(organizationId, postId, targetId, payload) {
    if (!targetId) {
      throw new Error("Publishing target ID is required.");
    }

    const response = await api.post(
      `${this.getPostPath(organizationId, postId)}targets/${targetId}/schedule/`,
      payload,
    );

    return response.data;
  }

  async publishPostNow(organizationId, postId) {
    const response = await api.post(
      `${this.getPostPath(organizationId, postId)}publish-now/`,
    );

    return response.data;
  }

  async publishPostTargetNow(organizationId, postId, targetId) {
    if (!targetId) {
      throw new Error("Publishing target ID is required.");
    }

    const response = await api.post(
      `${this.getPostPath(organizationId, postId)}targets/${targetId}/publish-now/`,
    );

    return response.data;
  }

  async retryPostTarget(organizationId, postId, targetId) {
    if (!targetId) {
      throw new Error("Publishing target ID is required.");
    }

    const response = await api.post(
      `${this.getPostPath(organizationId, postId)}targets/${targetId}/retry/`,
    );

    return response.data;
  }

  async deletePost(organizationId, postId) {
    const response = await api.delete(
      this.getPostPath(organizationId, postId),
    );

    return response.data;
  }

  async deletePostTarget(organizationId, postId, targetId) {
    if (!targetId) {
      throw new Error("Publishing target ID is required.");
    }

    const response = await api.delete(
      `${this.getPostPath(organizationId, postId)}targets/${targetId}/`,
    );

    return response.data;
  }
}

export default new PostService();
