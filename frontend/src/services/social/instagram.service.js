import api from "../../api/axios";

const instagramService = {
  // ==========================================================
  // START INSTAGRAM OAUTH
  // ==========================================================

  async startOAuth(organizationId) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    const response = await api.get("/integrations/instagram/oauth/start/", {
      params: {
        organization_id: organizationId,
      },
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
