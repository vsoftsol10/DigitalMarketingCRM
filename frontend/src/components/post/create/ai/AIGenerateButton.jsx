import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";

import { useFormContext } from "react-hook-form";

import PrimaryButton from "../../../ui/button/PrimaryButton";

import { useGenerateAICaption } from "../../../../hooks/mutations/useGenerateAICaption";

export default function AIGenerateButton({ setSuggestions }) {
  const { watch } = useFormContext();

  const { mutate, isPending } = useGenerateAICaption();

  function handleGenerate() {
    mutate(
      {
        prompt: watch("ai_prompt"),
        tone: watch("ai_tone"),
        length: watch("ai_length"),
        include_emoji: watch("ai_include_emoji"),
        include_hashtags: watch("ai_include_hashtags"),
        include_cta: watch("ai_include_cta"),
      },
      {
        onSuccess: (response) => {
          setSuggestions(response);
        },
      },
    );
  }

  return (
    <PrimaryButton
      startIcon={<AutoAwesomeRoundedIcon />}
      loading={isPending}
      onClick={handleGenerate}
    >
      Generate AI Caption
    </PrimaryButton>
  );
}
