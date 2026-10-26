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
        justifyContent: "flex-end",
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
          borderRadius: "14px",
          fontSize: 13.5,
          fontWeight: 600,
          textTransform: "none",
          border: "1px solid rgba(255,255,255,.7)",
          background:
            "linear-gradient(115deg, #A96BEA 0%, #7074ED 54%, #4A91ED 100%)",
          boxShadow:
            "0 7px 15px rgba(100,92,203,.25), 0 2px 5px rgba(65,101,210,.14), inset 0 1px 0 rgba(255,255,255,.46), inset 0 -2px 3px rgba(67,71,163,.16)",
          "&:hover": {
            background:
              "linear-gradient(115deg, #9D60E3 0%, #5E70E8 56%, #3D8FEA 100%)",
            boxShadow:
              "0 9px 17px rgba(100,92,203,.3), 0 3px 6px rgba(65,101,210,.18), inset 0 1px 0 rgba(255,255,255,.42)",
          },
          "&.Mui-disabled": {
            color: "rgba(255,255,255,.78)",
            background: "linear-gradient(115deg, #B993DD, #929BE1)",
          },
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
