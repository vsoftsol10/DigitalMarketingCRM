// import { CONTENT_PLANNER } from "../data/contentPlanner";

// class ContentPlannerService {
//   async getContentPlanner() {
//     return CONTENT_PLANNER;
//   }

//   async getIdea(id) {
//     /*
//       Later

//       GET /api/content-planner/:id/
//     */

//     return CONTENT_PLANNER.ideas.find((idea) => idea.id === id);
//   }

//   async createIdea(payload) {
//     /*
//       POST /api/content-planner/
//     */
//   }

//   async updateIdea(id, payload) {
//     /*
//       PUT /api/content-planner/:id/
//     */
//   }

//   async deleteIdea(id) {
//     CONTENT_PLANNER.ideas = CONTENT_PLANNER.ideas.filter(
//       (idea) => idea.id !== id,
//     );

//     return true;
//   }
// }

// export default new ContentPlannerService();

import api from "../api/axios";

class ContentPlannerService {
  // ============================================================
  // GET CONTENT PLANNER
  // ============================================================

  async getContentPlanner({ search = "", organization = "all" } = {}) {
    const params = {};

    if (search?.trim()) {
      params.search = search.trim();
    }

    if (organization && organization !== "all") {
      params.organization = organization;
    }

    const response = await api.get("/content-planner/", {
      params,
    });

    return response.data;
  }

  // ============================================================
  // GET SINGLE CONTENT IDEA
  // ============================================================

  async getIdea(ideaId) {
    if (!ideaId) {
      throw new Error("Content idea ID is required.");
    }

    const response = await api.get(`/content-planner/${ideaId}/`);

    return response.data;
  }

  // ============================================================
  // CREATE CONTENT IDEA
  // ============================================================

  async createIdea(payload) {
    if (!payload) {
      throw new Error("Content idea payload is required.");
    }

    const response = await api.post("/content-planner/", payload);

    return response.data;
  }

  // ============================================================
  // UPDATE CONTENT IDEA
  // ============================================================

  async updateIdea(ideaId, payload) {
    if (!ideaId) {
      throw new Error("Content idea ID is required.");
    }

    if (!payload) {
      throw new Error("Content idea payload is required.");
    }

    const response = await api.patch(`/content-planner/${ideaId}/`, payload);

    return response.data;
  }

  // ============================================================
  // DELETE CONTENT IDEA
  // ============================================================

  async deleteIdea(ideaId) {
    if (!ideaId) {
      throw new Error("Content idea ID is required.");
    }

    const response = await api.delete(`/content-planner/${ideaId}/`);

    return response.data;
  }
}

export default new ContentPlannerService();
