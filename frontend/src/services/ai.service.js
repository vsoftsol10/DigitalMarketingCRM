// import { AI_SUGGESTIONS } from "../data/ai";

// class AIService {
//   async generateCaption(payload) {
//     console.log("AI Payload:", payload);

//     // Simulate API delay
//     await new Promise((resolve) =>
//       setTimeout(resolve, 1200)
//     );

//     return AI_SUGGESTIONS;
//   }
// }

// export default new AIService();

import api from "../api/axios";

class AIService {
  async generateCaption(payload) {
    const response = await api.post("/ai/captions/generate/", payload);

    return response.data.data;
  }
}

export default new AIService();
