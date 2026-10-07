import api from "../api/axios";

function unwrap(response) {
  return response.data?.data;
}

const insightsService = {
  async getOrganizations({ signal } = {}) {
    return unwrap(await api.get("/insights/organizations/", { signal }));
  },

  async getAccounts(organizationId, { platform, signal } = {}) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    const response = await api.get(
      `/insights/organizations/${organizationId}/accounts/`,
      { params: platform ? { platform } : {}, signal },
    );
    return unwrap(response);
  },

  async getAccountSnapshot(organizationId, accountId, { since, until, platform, signal } = {}) {
    if (!organizationId || !accountId) {
      throw new Error("Organization and account IDs are required.");
    }

    const params = { since, until, platform };

    return unwrap(await api.get(
      `/insights/organizations/${organizationId}/accounts/${accountId}/snapshot/`,
      { params, signal },
    ));
  },

  async getContentSnapshot(organizationId, accountId, { since, until, platform, page = 1, signal } = {}) {
    if (!organizationId || !accountId) {
      throw new Error("Organization and account IDs are required.");
    }

    return unwrap(await api.get(
      `/insights/organizations/${organizationId}/accounts/${accountId}/snapshot/content/`,
      { params: { since, until, platform, page }, signal },
    ));
  },

  async requestSync(organizationId, accountId, {
    since,
    until,
    platform,
    forceRefresh = false,
    signal,
  } = {}) {
    if (!organizationId || !accountId) {
      throw new Error("Organization and account IDs are required.");
    }

    const response = await api.post(
      `/insights/organizations/${organizationId}/accounts/${accountId}/sync/`,
      { since, until, platform, force_refresh: forceRefresh },
      { signal },
    );
    return { data: unwrap(response), status: response.status };
  },
};

export default insightsService;
