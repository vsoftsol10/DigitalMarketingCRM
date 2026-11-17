// import api from "../../api/axios";

// import {
//   mapSocialAccount,
//   mapSocialAccounts,
// } from "./socialAccount.mapper";

// class SocialAccountService {
//   // ============================================================
//   // GET ORGANIZATION SOCIAL ACCOUNTS
//   // ============================================================

//   async getOrganizationSocialAccounts(organizationId) {
//     if (!organizationId) {
//       throw new Error("Organization ID is required.");
//     }

//     const response = await api.get(
//       `/organizations/${organizationId}/social-accounts/`,
//     );

//     return {
//       ...response.data,
//       data: mapSocialAccounts(response.data?.data),
//     };
//   }

//   // ============================================================
//   // GET SINGLE SOCIAL ACCOUNT
//   // ============================================================

//   async getSocialAccount(
//     organizationId,
//     socialAccountId,
//   ) {
//     if (!organizationId) {
//       throw new Error("Organization ID is required.");
//     }

//     if (!socialAccountId) {
//       throw new Error("Social account ID is required.");
//     }

//     const response = await api.get(
//       `/organizations/${organizationId}/social-accounts/${socialAccountId}/`,
//     );

//     return {
//       ...response.data,
//       data: mapSocialAccount(response.data?.data),
//     };
//   }

//   // ============================================================
//   // UPDATE SOCIAL ACCOUNT METADATA
//   // ============================================================

//   async updateSocialAccount(
//     organizationId,
//     socialAccountId,
//     payload,
//   ) {
//     if (!organizationId) {
//       throw new Error("Organization ID is required.");
//     }

//     if (!socialAccountId) {
//       throw new Error("Social account ID is required.");
//     }

//     if (!payload) {
//       throw new Error("Social account payload is required.");
//     }

//     const response = await api.patch(
//       `/organizations/${organizationId}/social-accounts/${socialAccountId}/`,
//       payload,
//     );

//     return {
//       ...response.data,
//       data: mapSocialAccount(response.data?.data),
//     };
//   }

//   // ============================================================
//   // DELETE SOCIAL ACCOUNT
//   // ============================================================

//   async deleteSocialAccount(
//     organizationId,
//     socialAccountId,
//   ) {
//     if (!organizationId) {
//       throw new Error("Organization ID is required.");
//     }

//     if (!socialAccountId) {
//       throw new Error("Social account ID is required.");
//     }

//     const response = await api.delete(
//       `/organizations/${organizationId}/social-accounts/${socialAccountId}/`,
//     );

//     return response.data;
//   }

// }

// export default new SocialAccountService();

import api from "../../api/axios";

import { mapSocialAccount, mapSocialAccounts } from "./socialAccount.mapper";

// ============================================================
// SOCIAL ACCOUNT SERVICE
// ============================================================

const socialAccountService = {
  // ==========================================================
  // GET ORGANIZATION SOCIAL ACCOUNTS
  // ==========================================================

  getOrganizationSocialAccounts: async (organizationId, { signal } = {}) => {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    const response = await api.get(
      `/organizations/${organizationId}/social-accounts/`,
      { signal },
    );

    if (!response || !response.data) {
      throw new Error("The social account response was not returned.");
    }

    if (response.data?.success !== true) {
      const message = typeof response.data.message === "string"
        ? response.data.message.trim()
        : "";
      throw new Error(message || "Unable to load social accounts.");
    }

    if (!Array.isArray(response.data.data)) {
      throw new Error("Social account data was not returned in the expected format.");
    }

    const hasMalformedAccount = response.data.data.some((account) => (
      !account
      || typeof account !== "object"
      || Array.isArray(account)
      || typeof account.id !== "string"
      || !account.id.trim()
      || typeof account.platform !== "string"
      || !account.platform.trim()
    ));

    if (hasMalformedAccount) {
      throw new Error("Social account data included an invalid account entry.");
    }

    return {
      ...response.data,
      data: mapSocialAccounts(response.data.data),
    };
  },

  // ==========================================================
  // GET SINGLE SOCIAL ACCOUNT
  // ==========================================================

  getSocialAccount: async (organizationId, socialAccountId) => {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    if (!socialAccountId) {
      throw new Error("Social account ID is required.");
    }

    const response = await api.get(
      `/organizations/${organizationId}/social-accounts/${socialAccountId}/`,
    );

    return {
      ...response.data,
      data: mapSocialAccount(response.data?.data),
    };
  },

  // ==========================================================
  // UPDATE SOCIAL ACCOUNT
  // ==========================================================

  updateSocialAccount: async (organizationId, socialAccountId, payload) => {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    if (!socialAccountId) {
      throw new Error("Social account ID is required.");
    }

    if (!payload) {
      throw new Error("Social account payload is required.");
    }

    const response = await api.patch(
      `/organizations/${organizationId}/social-accounts/${socialAccountId}/`,
      payload,
    );

    return {
      ...response.data,
      data: mapSocialAccount(response.data?.data),
    };
  },

  // ==========================================================
  // DISCONNECT SOCIAL ACCOUNT
  // ==========================================================

  disconnectSocialAccount: async (organizationId, socialAccountId) => {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    if (!socialAccountId) {
      throw new Error("Social account ID is required.");
    }

    const response = await api.post(
      `/organizations/${organizationId}/social-accounts/${socialAccountId}/disconnect/`,
    );

    return {
      ...response.data,
      data: mapSocialAccount(response.data?.data),
    };
  },

  // ==========================================================
  // DELETE SOCIAL ACCOUNT
  // ==========================================================

  deleteSocialAccount: async (organizationId, socialAccountId) => {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    if (!socialAccountId) {
      throw new Error("Social account ID is required.");
    }

    const response = await api.delete(
      `/organizations/${organizationId}/social-accounts/${socialAccountId}/`,
    );

    return response.data;
  },
};

export default socialAccountService;
