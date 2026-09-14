import api from "../../api/axios";

const metaService = {
  // ==========================================================
  // START FACEBOOK OAUTH
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
      throw new Error("Facebook authorization URL was not returned.");
    }

    window.location.assign(authorizationUrl);

    return response.data;
  },

  // ==========================================================
  // GET FACEBOOK PAGE SELECTION
  // ==========================================================

  async getOAuthSelection(organizationId, selectionKey) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    if (!selectionKey) {
      throw new Error("Facebook selection key is required.");
    }

    const response = await api.get("/integrations/meta/oauth/selection/", {
      params: {
        organization_id: organizationId,
        selection_key: selectionKey,
      },
    });

    if (!response?.data?.success) {
      throw new Error(
        response?.data?.message || "Unable to load Facebook Pages.",
      );
    }

    return response.data;
  },

  // ==========================================================
  // CONFIRM FACEBOOK PAGE SELECTION
  // ==========================================================

  async confirmOAuthSelection(organizationId, selectionKey, pageId) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    if (!selectionKey) {
      throw new Error("Facebook selection key is required.");
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
        response?.data?.message ||
          "Unable to connect the selected Facebook Page.",
      );
    }

    return response.data;
  },
};

export default metaService;