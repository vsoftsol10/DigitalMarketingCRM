import api from "../api/axios";

class DashboardService {
  async getDashboard() {
    const response = await api.get("/dashboard/");

    return response.data?.data;
  }
}

export default new DashboardService();
