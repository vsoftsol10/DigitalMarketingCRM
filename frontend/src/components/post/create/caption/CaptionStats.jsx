import { Box, Typography } from "@mui/material";
import { useFormContext } from "react-hook-form";

import { TYPOGRAPHY } from "../../../../theme/typography";

export default function CaptionStats() {
  const { watch } = useFormContext();

  const caption = watch("caption") || "";

  const characterCount = caption.length;

  const wordCount = caption.trim().split(/\s+/).filter(Boolean).length;

  const readingTime = Math.max(1, Math.ceil((wordCount / 200) * 60));
  
  const MAX_CHARACTERS = 2200;

  const usage = characterCount / MAX_CHARACTERS;

  let characterColor = "#64748B";

  if (usage >= 1) {
    characterColor = "#DC2626";
  } else if (usage >= 0.9) {
    characterColor = "#F59E0B";
  }
  return (
    <Box
      sx={{
        mt: 2,

        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",

        flexWrap: "wrap",
        gap: 2,
      }}
    >
      <Typography
        sx={{
          ...TYPOGRAPHY.helperText,
          color: characterColor,
          fontWeight: 600,
        }}
      >
        {characterCount} / {MAX_CHARACTERS} Characters
      </Typography>

      <Typography sx={TYPOGRAPHY.helperText}>Words: {wordCount}</Typography>

      <Typography sx={TYPOGRAPHY.helperText}>
        Reading Time: ~{readingTime}s
      </Typography>
    </Box>
  );
}
