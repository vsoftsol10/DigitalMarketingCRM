import api from "../api/axios";

const reportsService = {
  async preview(payload) {
    const response = await api.post("/reports/insights/preview/", payload);
    return response.data?.data;
  },

  async renderPng({ renderToken, html }) {
    const response = await api.post("/reports/insights/png/", {
      render_token: renderToken,
      html,
    }, { responseType: "blob" });
    return response.data;
  },
};

export default reportsService;
