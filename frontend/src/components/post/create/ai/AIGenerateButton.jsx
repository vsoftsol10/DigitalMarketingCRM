import { AutoAwesomeRounded, RefreshRounded } from "@mui/icons-material";

import { Box } from "@mui/material";

import { useFormContext } from "react-hook-form";

import PrimaryButton from "../../../ui/button/PrimaryButton";

import { useGenerateAICaption } from "../../../../hooks/mutations/useGenerateAICaption";

export default function AIGenerateButton({
  setSuggestions,
  hasSuggestion = false,
}) {
  const { watch } = useFormContext();

  const { mutate, isPending } = useGenerateAICaption();

  function handleGenerate() {
    const payload = {
      prompt: watch("ai_prompt"),
      tone: watch("ai_tone"),
      length: watch("ai_length"),
      include_emoji: watch("ai_include_emoji"),
      include_hashtags: watch("ai_include_hashtags"),
      include_cta: watch("ai_include_cta"),
    };

    mutate(payload, {
      onSuccess: (response) => {
        let results = [];

        if (Array.isArray(response)) {
          results = response;
        } else if (Array.isArray(response?.data)) {
          results = response.data;
        } else if (Array.isArray(response?.suggestions)) {
          results = response.suggestions;
        } else if (Array.isArray(response?.data?.suggestions)) {
          results = response.data.suggestions;
        }

        // Only one AI caption should be displayed.
        setSuggestions(results.slice(0, 1));
      },
    });
  }

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "flex-start",
        mt: 0.5,
      }}
    >
      <PrimaryButton
        type="button"
        startIcon={hasSuggestion ? <RefreshRounded /> : <AutoAwesomeRounded />}
        loading={isPending}
        onClick={handleGenerate}
        sx={{
          width: "auto",
          minWidth: 0,
          height: 40,
          px: 2.25,
          borderRadius: "10px",
          fontSize: 13.5,
          fontWeight: 600,
          textTransform: "none",
        }}
      >
        {isPending
          ? "Generating..."
          : hasSuggestion
            ? "Regenerate"
            : "Generate Caption"}
      </PrimaryButton>
    </Box>
  );
}
