import api from "../../api/axios";

class OrganizationService {
  // ============================================================
  // LIST ORGANIZATIONS
  // ============================================================

  async getOrganizations({
    search = "",
    status = "",
    subscriptionStatus = "",
    ordering = "-created_at",
    page = 1,
    pageSize = 10,
  } = {}) {
    const params = {
      page,
      page_size: pageSize,
      ordering,
    };

    if (search.trim()) {
      params.search = search.trim();
    }

    if (status) {
      params.status = status;
    }

    if (subscriptionStatus) {
      params.subscription_status = subscriptionStatus;
    }

    const response = await api.get("/organizations/", {
      params,
    });

    return response.data;
  }

  // ============================================================
  // GET SINGLE ORGANIZATION
  // ============================================================

  async getOrganization(organizationId) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    const response = await api.get(`/organizations/${organizationId}/`);

    return response.data;
  }

  // ============================================================
  // GET ORGANIZATION OVERVIEW
  // ============================================================

  async getOrganizationOverview(organizationId) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    const response = await api.get(
      `/organizations/${organizationId}/overview/`,
    );

    return response.data;
  }

  // ============================================================
  // CREATE ORGANIZATION
  // ============================================================

  async createOrganization(payload) {
    if (!payload) {
      throw new Error("Organization payload is required.");
    }

    const response = await api.post("/organizations/", payload);

    return response.data;
  }

  // ============================================================
  // UPDATE ORGANIZATION
  // ============================================================

  async updateOrganization(organizationId, payload) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    if (!payload) {
      throw new Error("Organization payload is required.");
    }

    const response = await api.patch(
      `/organizations/${organizationId}/`,
      payload,
    );

    return response.data;
  }

  // ============================================================
  // DELETE ORGANIZATION
  // ============================================================

  async deleteOrganization(organizationId) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    const response = await api.delete(`/organizations/${organizationId}/`);

    return response.data;
  }

  // ============================================================
  // START NEW SUBSCRIPTION
  // ============================================================

  async startSubscription(organizationId, { plan, billing_cycle }) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    if (!plan) {
      throw new Error("Plan ID is required.");
    }

    if (!billing_cycle) {
      throw new Error("Billing cycle is required.");
    }

    const response = await api.post(
      `/organizations/${organizationId}/subscription/start/`,
      {
        plan,
        billing_cycle,
      },
    );

    return response.data;
  }

  // ============================================================
  // RENEW SUBSCRIPTION
  // ============================================================

  async renewSubscription(organizationId, { billing_cycle } = {}) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    const payload = {};

    if (billing_cycle) {
      payload.billing_cycle = billing_cycle;
    }

    const response = await api.post(
      `/organizations/${organizationId}/subscription/renew/`,
      payload,
    );

    return response.data;
  }

  // ============================================================
  // CHANGE SUBSCRIPTION PLAN
  // ============================================================

  async changeSubscriptionPlan(organizationId, { plan, billing_cycle }) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    if (!plan) {
      throw new Error("Plan ID is required.");
    }

    if (!billing_cycle) {
      throw new Error("Billing cycle is required.");
    }

    const response = await api.post(
      `/organizations/${organizationId}/subscription/change-plan/`,
      {
        plan,
        billing_cycle,
      },
    );

    return response.data;
  }

  // ============================================================
  // CANCEL SUBSCRIPTION
  // ============================================================

  async cancelSubscription(organizationId) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    const response = await api.post(
      `/organizations/${organizationId}/subscription/cancel/`,
      {},
    );

    return response.data;
  }

  // ============================================================
  // GET SUBSCRIPTION HISTORY
  // ============================================================

  async getSubscriptionHistory(organizationId) {
    if (!organizationId) {
      throw new Error("Organization ID is required.");
    }

    const response = await api.get(
      `/organizations/${organizationId}/subscription/history/`,
    );

    return response.data;
  }
}

export default new OrganizationService();
