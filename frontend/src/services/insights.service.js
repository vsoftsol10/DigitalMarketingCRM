import { INSIGHTS } from "../data/insights";

class InsightsService {
  async getInsights() {
    /*
      Later

      GET /api/insights/
    */

    return INSIGHTS;
  }
}

export default new InsightsService();