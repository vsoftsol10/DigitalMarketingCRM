// // import api from "../../api/axios";

// // const metaService = {
// //   /**
// //    * Start Meta Login for Business OAuth.
// //    *
// //    * Backend returns the Meta authorization URL.
// //    * Browser is then redirected directly to Meta.
// //    *
// //    * No Page selection happens inside our frontend.
// //    */
// //   async startOAuth(organizationId) {
// //     if (!organizationId) {
// //       throw new Error("Organization ID is required.");
// //     }

// //     const response = await api.get("/integrations/meta/oauth/start/", {
// //       params: {
// //         organization_id: organizationId,
// //       },
// //     });

// //     const authorizationUrl = response?.data?.authorization_url;

// //     if (!authorizationUrl) {
// //       throw new Error("Meta authorization URL was not returned.");
// //     }

// //     window.location.assign(authorizationUrl);

// //     return response.data;
// //   },
// // };

// // export default metaService;

// import api from "../../api/axios";

// const metaService = {
//   async startOAuth(organizationId) {
//     if (!organizationId) {
//       throw new Error("Organization ID is required.");
//     }

//     const response = await api.get("/integrations/meta/oauth/start/", {
//       params: {
//         organization_id: organizationId,
//       },
//     });

//     const authorizationUrl = response?.data?.authorization_url;

//     if (!authorizationUrl) {
//       throw new Error("Meta authorization URL was not returned.");
//     }

//     window.location.assign(authorizationUrl);

//     return response.data;
//   },
// };

// export default metaService;


import api from "../../api/axios";

const metaService = {
  // ==========================================================
  // START OAUTH
  // ==========================================================

  async startOAuth(organizationId) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    const response = await api.get("/integrations/meta/oauth/start/", {
      params: {
        organization_id: organizationId,
      },
    });

    const authorizationUrl = response?.data?.authorization_url;

    if (!authorizationUrl) {
      throw new Error("Meta authorization URL was not returned.");
    }

    window.location.assign(authorizationUrl);

    return response.data;
  },

  // ==========================================================
  // GET PAGE SELECTION
  // ==========================================================

  async getOAuthSelection(organizationId, selectionKey) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    if (!selectionKey) {
      throw new Error("Meta selection key is required.");
    }

    const response = await api.get("/integrations/meta/oauth/selection/", {
      params: {
        organization_id: organizationId,
        selection_key: selectionKey,
      },
    });

    if (!response?.data?.success) {
      throw new Error(response?.data?.message || "Unable to load Meta Pages.");
    }

    return response.data;
  },

  // ==========================================================
  // CONFIRM PAGE SELECTION
  // ==========================================================

  async confirmOAuthSelection(organizationId, selectionKey, pageId) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    if (!selectionKey) {
      throw new Error("Meta selection key is required.");
    }

    if (!pageId) {
      throw new Error("Facebook Page ID is required.");
    }

    const response = await api.post(
      "/integrations/meta/oauth/selection/confirm/",
      {
        organization_id: organizationId,
        selection_key: selectionKey,
        page_id: pageId,
      },
    );

    if (!response?.data?.success) {
      throw new Error(
        response?.data?.message || "Unable to connect the selected Meta Page.",
      );
    }

    return response.data;
  },
};

export default metaService;
