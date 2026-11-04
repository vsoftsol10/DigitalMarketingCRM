import api from "../../api/axios";

const requireData = (response, fallbackMessage) => {
  if (!response?.data?.success) {
    throw new Error(response?.data?.message || fallbackMessage);
  }
  return response.data.data;
};

const sessionCredential = (token, type = "acceptance") => (
  type === "resumption"
    ? { resumption_token: token }
    : { acceptance_token: token }
);

const socialInvitationService = {
  async validate(token) {
    return requireData(
      await api.post("/social-account-invitations/validate/", { token }),
      "Unable to validate this invitation.",
    );
  },

  async claim(token, platforms) {
    return requireData(
      await api.post("/social-account-invitations/claim/", { token, platforms }),
      "Unable to start this invitation.",
    );
  },

  async resumePlatform(resumptionToken, platform) {
    return requireData(
      await api.post("/social-account-invitations/resume/", {
        resumption_token: resumptionToken,
        platform,
      }),
      "This platform invitation link is invalid or no longer available.",
    );
  },

  async cancel(acceptanceToken) {
    return requireData(
      await api.post("/social-account-invitations/cancel/", {
        acceptance_token: acceptanceToken,
      }),
      "Unable to cancel this invitation session.",
    );
  },

  async complete(acceptanceToken, credentialType = "acceptance") {
    return requireData(
      await api.post("/social-account-invitations/complete/", sessionCredential(acceptanceToken, credentialType)),
      "Unable to complete this invitation.",
    );
  },

  async startFacebook(acceptanceToken) {
    const data = requireData(
      await api.post("/integrations/meta/invitation/oauth/start/", {
        acceptance_token: acceptanceToken,
      }),
      "Facebook authorization is unavailable.",
    );
    if (!data?.authorization_url) {
      throw new Error("Facebook authorization URL was not returned.");
    }
    return data.authorization_url;
  },

  async startFacebookFromResumption(resumptionToken) {
    const data = requireData(
      await api.post("/integrations/meta/invitation/oauth/start/", {
        resumption_token: resumptionToken,
      }),
      "Facebook authorization is unavailable.",
    );
    if (!data?.authorization_url || !data?.invitation) {
      throw new Error("Facebook authorization session was not returned.");
    }
    return data;
  },

  async getFacebookPages(acceptanceToken, selectionKey, credentialType = "acceptance") {
    return requireData(
      await api.post("/integrations/meta/invitation/oauth/selection/", {
        ...sessionCredential(acceptanceToken, credentialType),
        selection_key: selectionKey,
      }),
      "Unable to load Facebook Pages.",
    );
  },

  async addFacebookPage(acceptanceToken, selectionKey, pageId, credentialType = "acceptance") {
    return requireData(
      await api.post("/integrations/meta/invitation/oauth/selection/add/", {
        ...sessionCredential(acceptanceToken, credentialType),
        selection_key: selectionKey,
        page_id: pageId,
      }),
      "Unable to connect this Facebook Page.",
    );
  },

  async startInstagram(acceptanceToken) {
    const data = requireData(
      await api.post("/integrations/instagram/invitation/oauth/start/", {
        acceptance_token: acceptanceToken,
      }),
      "Instagram authorization is unavailable.",
    );
    if (!data?.authorization_url) {
      throw new Error("Instagram authorization URL was not returned.");
    }
    return data.authorization_url;
  },

  async startInstagramFromResumption(resumptionToken) {
    const data = requireData(
      await api.post("/integrations/instagram/invitation/oauth/start/", {
        resumption_token: resumptionToken,
      }),
      "Instagram authorization is unavailable.",
    );
    if (!data?.authorization_url || !data?.invitation) {
      throw new Error("Instagram authorization session was not returned.");
    }
    return data;
  },

  async getInstagramPreview(acceptanceToken, selectionKey, credentialType = "acceptance") {
    return requireData(
      await api.post("/integrations/instagram/invitation/oauth/preview/", {
        ...sessionCredential(acceptanceToken, credentialType),
        selection_key: selectionKey,
      }),
      "Unable to load the Instagram profile preview.",
    );
  },

  async confirmInstagram(acceptanceToken, selectionKey, credentialType = "acceptance") {
    return requireData(
      await api.post("/integrations/instagram/invitation/oauth/confirm/", {
        ...sessionCredential(acceptanceToken, credentialType),
        selection_key: selectionKey,
      }),
      "Unable to connect this Instagram account.",
    );
  },

  async declineInstagram(acceptanceToken, selectionKey, credentialType = "acceptance") {
    return requireData(
      await api.post("/integrations/instagram/invitation/oauth/decline/", {
        ...sessionCredential(acceptanceToken, credentialType),
        selection_key: selectionKey,
      }),
      "Unable to decline this Instagram authorization.",
    );
  },
};

export default socialInvitationService;
