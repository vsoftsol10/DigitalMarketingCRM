// reconect change 

// import api from "../../api/axios";

// const instagramService = {
//   // ==========================================================
//   // START INSTAGRAM OAUTH
//   // ==========================================================

//   async startOAuth(organizationId) {
//     if (!organizationId) {
//       throw new Error("Organization ID is required.");
//     }

//     const response = await api.get("/integrations/instagram/oauth/start/", {
//       params: {
//         organization_id: organizationId,
//       },
//     });

//     const authorizationUrl = response?.data?.data?.authorization_url;

//     if (!authorizationUrl) {
//       throw new Error(
//         response?.data?.message ||
//           "Instagram authorization URL was not returned.",
//       );
//     }

//     window.location.assign(authorizationUrl);

//     return response.data;
//   },
// };

// export default instagramService;

import api from "../../api/axios";

const instagramService = {
  // ==========================================================
  // START INSTAGRAM OAUTH
  // ==========================================================

  async startOAuth(organizationId, options = {}) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    const action = options?.action;
    const socialAccountId = options?.socialAccountId;

    // ========================================================
    // VALIDATE ACTION
    // ========================================================

    if (action && action !== "connect" && action !== "reconnect") {
      throw new Error("Invalid Instagram OAuth action.");
    }

    // ========================================================
    // RECONNECT REQUIRES TARGET ACCOUNT
    // ========================================================

    if (action === "reconnect" && !socialAccountId) {
      throw new Error("Social account ID is required for Instagram reconnect.");
    }

    const params = {
      organization_id: organizationId,
    };

    // ========================================================
    // OPTIONAL OAUTH ACTION
    // ========================================================

    if (action) {
      params.action = action;
    }

    // ========================================================
    // RECONNECT TARGET
    // ========================================================

    if (socialAccountId) {
      params.social_account_id = socialAccountId;
    }

    const response = await api.get("/integrations/instagram/oauth/start/", {
      params,
    });

    const authorizationUrl = response?.data?.data?.authorization_url;

    if (!authorizationUrl) {
      throw new Error(
        response?.data?.message ||
          "Instagram authorization URL was not returned.",
      );
    }

    window.location.assign(authorizationUrl);

    return response.data;
  },
};

export default instagramService;
