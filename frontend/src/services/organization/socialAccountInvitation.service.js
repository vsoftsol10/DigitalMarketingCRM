import api from "../../api/axios";

const readData = (response) => {
  if (response?.data?.success === false) {
    const error = new Error(response.data.message || "The invitation request could not be completed.");
    error.response = { data: response.data, status: response.status };
    throw error;
  }
  return response?.data?.data;
};

const socialAccountInvitationService = {
  async list(organizationId) {
    const response = await api.get(
      `/organizations/${organizationId}/social-account-invitations/`,
    );

    if (response?.data?.success !== true || !Array.isArray(response.data.data)) {
      throw new Error("Invitations were not returned in the expected format.");
    }

    const hasMalformedInvitation = response.data.data.some((invitation) => (
      !invitation
      || typeof invitation !== "object"
      || Array.isArray(invitation)
      || typeof invitation.id !== "string"
      || !invitation.id.trim()
      || !["email", "share_link"].includes(invitation.mode)
      || typeof invitation.status !== "string"
      || !invitation.status.trim()
      || !Array.isArray(invitation.platforms)
      || !invitation.platforms.every((platform) => (
        typeof platform === "string" && Boolean(platform.trim())
      ))
      || typeof invitation.expires_at !== "string"
      || !Number.isFinite(Date.parse(invitation.expires_at))
    ));

    if (hasMalformedInvitation) {
      throw new Error("Invitations included an invalid invitation entry.");
    }

    return response.data.data;
  },

  async createShareLink(organizationId, platforms) {
    return readData(await api.post(
      `/organizations/${organizationId}/social-account-invitations/share-link/`,
      { platforms },
    ));
  },

  async createEmailInvitation(organizationId, email, platforms) {
    return readData(await api.post(
      `/organizations/${organizationId}/social-account-invitations/email/`,
      { email, platforms },
    ));
  },

  async sendEmail(organizationId, invitationId) {
    return readData(await api.post(
      `/organizations/${organizationId}/social-account-invitations/${invitationId}/email/send/`,
      {},
    ));
  },

  async retryEmail(organizationId, invitationId) {
    return readData(await api.post(
      `/organizations/${organizationId}/social-account-invitations/${invitationId}/email/retry/`,
      {},
    ));
  },

  async resendEmail(organizationId, invitationId) {
    return readData(await api.post(
      `/organizations/${organizationId}/social-account-invitations/${invitationId}/email/resend/`,
      {},
    ));
  },

  async revoke(organizationId, invitationId) {
    return readData(await api.post(
      `/organizations/${organizationId}/social-account-invitations/${invitationId}/revoke/`,
      {},
    ));
  },
};

export default socialAccountInvitationService;
