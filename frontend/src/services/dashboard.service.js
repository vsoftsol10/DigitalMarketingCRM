import { DASHBOARD } from "../data/dashboard";

class DashboardService {
  async getDashboard() {
    /*
      Later

      GET /api/dashboard/
    */

    return DASHBOARD;
  }
}

export default new DashboardService();
