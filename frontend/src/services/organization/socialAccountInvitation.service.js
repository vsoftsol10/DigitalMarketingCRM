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
    return readData(await api.get(
      `/organizations/${organizationId}/social-account-invitations/`,
    )) || [];
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
