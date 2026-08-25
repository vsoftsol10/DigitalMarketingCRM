import { Alert, Stack } from "@mui/material";

import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";

import { useFormContext } from "react-hook-form";

import AISuggestionCard from "./AISuggestionCard";

export default function AISuggestions({ suggestions }) {
  const { setValue } = useFormContext();

  function handleUseCaption(suggestion) {
    setValue("caption", suggestion.caption, {
      shouldDirty: true,
      shouldValidate: true,
    });
  }

  if (!suggestions.length) {
    return (
      <Alert
        icon={<AutoAwesomeRoundedIcon />}
        severity="info"
        sx={{
          mt: 2,
          borderRadius: "16px",
        }}
      >
        Generate an AI caption to see suggestions.
      </Alert>
    );
  }

  return (
    <Stack
      spacing={2}
      sx={{
        mt: 2,
      }}
    >
      {suggestions.map((suggestion) => (
        <AISuggestionCard
          key={suggestion.id}
          suggestion={suggestion}
          onUse={handleUseCaption}
        />
      ))}
    </Stack>
  );
}
