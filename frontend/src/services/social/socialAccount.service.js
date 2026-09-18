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

    return {
      ...response.data,
      data: mapSocialAccounts(response.data?.data),
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
