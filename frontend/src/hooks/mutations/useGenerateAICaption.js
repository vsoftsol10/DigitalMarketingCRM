import { useMutation } from "@tanstack/react-query";

import aiService from "../../services/ai.service";

export function useGenerateAICaption() {
  return useMutation({
    mutationFn: (payload) =>
      aiService.generateCaption(payload),
  });
}