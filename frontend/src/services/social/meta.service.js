// import api from "../../api/axios";

// const metaService = {
//   /**
//    * Start Meta Login for Business OAuth.
//    *
//    * Backend returns the Meta authorization URL.
//    * Browser is then redirected directly to Meta.
//    *
//    * No Page selection happens inside our frontend.
//    */
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
};

export default metaService;
