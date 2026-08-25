import settingsApi from "../api/settings/settings.api";

// function normalizeProfile(data) {
//   if (!data) {
//     return null;
//   }

//   return {
//     id: data.id || null,

//     email: data.email || "",

//     firstName:
//       data.first_name || "",

//     lastName:
//       data.last_name || "",

//     fullName:
//       data.full_name || "",

//     phone:
//       data.phone || "",

//     profileImage:
//       data.profile_image || null,
//   };
// }

function normalizeProfile(data) {
  if (!data) {
    return null;
  }

  return {
    id: data.id || null,

    email: data.email || "",

    firstName: data.first_name || "",

    lastName: data.last_name || "",

    fullName: data.full_name || "",

    phone: data.phone || "",

    profileImage: data.profile_image || null,
  };
}

const settingsService = {
  /**
   * Fetch current user profile.
   */
  async getProfile() {
    const response = await settingsApi.getProfile();

    return normalizeProfile(response?.data);
  },

  /**
   * Update current user profile.
   */
  async updateProfile(data) {
    const response = await settingsApi.updateProfile(data);

    return normalizeProfile(response?.data);
  },

  /**
   * Change current user password.
   */
  async changePassword(data) {
    const response = await settingsApi.changePassword(data);

    return response;
  },

  /**
   * Logout current user.
   */
  async logout(refreshToken) {
    return settingsApi.logout(refreshToken);
  },
};

export default settingsService;
