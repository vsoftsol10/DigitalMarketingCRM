// const MOCK_DELAY = 300;

// let MOCK_PLANS = [
//   {
//     id: "plan_basic",
//     name: "Basic",
//     description:
//       "Perfect for startups and small businesses looking to build their online presence.",
//     type: "Basic",
//     status: "active",
//     billing_cycle: "monthly",
//     monthly_price: 9999,
//     yearly_price: 99999,

//     limits: {
//       accounts: 3,
//       posts: 50,
//       videos: 20,
//       ads: 5,
//       storage_gb: 10,
//       dm_automations: 10,
//     },

//     highlights: "",
//   },

//   {
//     id: "plan_professional",
//     name: "Professional",
//     description:
//       "Ideal for growing brands that need more content output and creative support.",
//     type: "Professional",
//     status: "active",
//     billing_cycle: "monthly",
//     monthly_price: 19999,
//     yearly_price: 199999,

//     limits: {
//       accounts: 8,
//       posts: 150,
//       videos: 60,
//       ads: 15,
//       storage_gb: 50,
//       dm_automations: 25,
//     },

//     highlights: "",
//   },

//   {
//     id: "plan_premium",
//     name: "Premium",
//     description:
//       "For established agencies managing multiple clients with high content volume.",
//     type: "Premium",
//     status: "active",
//     billing_cycle: "monthly",
//     monthly_price: 29999,
//     yearly_price: 299999,

//     limits: {
//       accounts: 15,
//       posts: 300,
//       videos: 120,
//       ads: 30,
//       storage_gb: 100,
//       dm_automations: 50,
//     },

//     highlights: "",
//   },

//   {
//     id: "plan_advanced",
//     name: "Advanced",
//     description:
//       "For large teams with advanced workflows and higher content demands.",
//     type: "Advanced",
//     status: "active",
//     billing_cycle: "monthly",
//     monthly_price: 49999,
//     yearly_price: 499999,

//     limits: {
//       accounts: 30,
//       posts: 800,
//       videos: 250,
//       ads: 60,
//       storage_gb: 250,
//       dm_automations: 100,
//     },

//     highlights: "",
//   },

//   {
//     id: "plan_custom",
//     name: "Custom",
//     description: "Tailored plan with flexible limits for unique requirements.",
//     type: "Custom",
//     status: "inactive",
//     billing_cycle: "monthly",
//     monthly_price: 0,
//     yearly_price: 0,

//     limits: {
//       accounts: 0,
//       posts: 0,
//       videos: 0,
//       ads: 0,
//       storage_gb: 0,
//       dm_automations: 0,
//     },

//     highlights: "",
//   },
// ];

// function delay(value) {
//   return new Promise((resolve) => setTimeout(() => resolve(value), MOCK_DELAY));
// }

// async function getPlans() {
//   /*
//     Later

//     const { data } = await api.get("/plans");
//     return data;
//   */

//   return delay(MOCK_PLANS);
// }

// async function getPlan(planId) {
//   /*
//     Later

//     const { data } = await api.get(`/plans/${planId}`);
//     return data;
//   */

//   const plan = MOCK_PLANS.find((item) => item.id === planId) || null;

//   return delay(plan);
// }

// async function createPlan(data) {
//   /*
//     Later

//     const response = await api.post("/plans", data);
//     return response.data;
//   */

//   const newPlan = {
//     id: `plan_${Date.now()}`,
//     ...data,
//   };

//   MOCK_PLANS = [...MOCK_PLANS, newPlan];

//   return delay(newPlan);
// }

// async function updatePlan(planId, data) {
//   /*
//     Later

//     const response = await api.put(`/plans/${planId}`, data);
//     return response.data;
//   */

//   MOCK_PLANS = MOCK_PLANS.map((item) =>
//     item.id === planId ? { ...item, ...data } : item,
//   );

//   return delay(MOCK_PLANS.find((item) => item.id === planId));
// }

// async function deletePlan(planId) {
//   /*
//     Later

//     await api.delete(`/plans/${planId}`);
//   */

//   MOCK_PLANS = MOCK_PLANS.filter((item) => item.id !== planId);

//   return delay(true);
// }

// export default {
//   getPlans,
//   getPlan,
//   createPlan,
//   updatePlan,
//   deletePlan,
// };

import api from "../api/axios";

class PlansService {
  // ============================================================
  // LIST PLANS
  // ============================================================

  async getPlans({
    status = "",
    type = "",
    search = "",
    ordering = "-created_at",
  } = {}) {
    const params = {
      ordering,
    };

    if (status) {
      params.status = status;
    }

    if (type) {
      params.type = type;
    }

    if (search.trim()) {
      params.search = search.trim();
    }

    const response = await api.get("/plans/", {
      params,
    });

    return response.data?.data || [];
  }

  // ============================================================
  // GET SINGLE PLAN
  // ============================================================

  async getPlan(planId) {
    if (!planId) {
      throw new Error("Plan ID is required.");
    }

    const response = await api.get(`/plans/${planId}/`);

    return response.data?.data || null;
  }

  // ============================================================
  // CREATE PLAN
  // ============================================================

  async createPlan(payload, { custom = false } = {}) {
    if (!payload) {
      throw new Error("Plan payload is required.");
    }

    const params = custom ? { type: "custom" } : undefined;

    const response = await api.post("/plans/", payload, {
      params,
    });

    return response.data?.data;
  }

  // ============================================================
  // UPDATE PLAN
  // ============================================================

  async updatePlan(planId, payload) {
    if (!planId) {
      throw new Error("Plan ID is required.");
    }

    if (!payload) {
      throw new Error("Plan payload is required.");
    }

    const response = await api.patch(`/plans/${planId}/`, payload);

    return response.data?.data;
  }

  // ============================================================
  // DELETE PLAN
  // ============================================================

  async deletePlan(planId) {
    if (!planId) {
      throw new Error("Plan ID is required.");
    }

    const response = await api.delete(`/plans/${planId}/`);

    return response.data;
  }
}

export default new PlansService();
