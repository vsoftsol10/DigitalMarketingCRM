import api from "../axios";

const settingsApi = {
  // ==========================================
  // GET CURRENT PROFILE
  // ==========================================

  async getProfile() {
    const response = await api.get("/auth/me/");

    return response.data;
  },

  // ==========================================
  // UPDATE CURRENT PROFILE
  // ==========================================

  async updateProfile(data) {
    const formData = new FormData();

    // ------------------------------------------
    // Text fields
    // ------------------------------------------

    if (data.first_name !== undefined) {
      formData.append(
        "first_name",
        data.first_name,
      );
    }

    if (data.last_name !== undefined) {
      formData.append(
        "last_name",
        data.last_name,
      );
    }

    if (data.phone !== undefined) {
      formData.append(
        "phone",
        data.phone,
      );
    }

    // ------------------------------------------
    // Profile image
    // ------------------------------------------

    if (data.profile_image instanceof File) {
      formData.append(
        "profile_image",
        data.profile_image,
        data.profile_image.name,
      );
    }

    // ------------------------------------------
    // PATCH request
    // ------------------------------------------

    const response = await api.patch(
      "/auth/me/",
      formData,
    );

    return response.data;
  },

  // ==========================================
  // CHANGE PASSWORD
  // ==========================================

  async changePassword(data) {
    const response = await api.post(
      "/auth/change-password/",
      data,
    );

    return response.data;
  },

  // ==========================================
  // LOGOUT
  // ==========================================

  async logout(refreshToken) {
    const response = await api.post(
      "/auth/logout/",
      {
        refresh: refreshToken,
      },
    );

    return response.data;
  },
};

export default settingsApi;