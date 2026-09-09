// import { Box, Typography } from "@mui/material";
// import { useFormContext } from "react-hook-form";

// import { TYPOGRAPHY } from "../../../../theme/typography";

// export default function CaptionStats() {
//   const { watch } = useFormContext();

//   const caption = watch("caption") || "";

//   const characterCount = caption.length;

//   const wordCount = caption.trim().split(/\s+/).filter(Boolean).length;

//   const readingTime = Math.max(1, Math.ceil((wordCount / 200) * 60));
  
//   const MAX_CHARACTERS = 2200;

//   const usage = characterCount / MAX_CHARACTERS;

//   let characterColor = "#64748B";

//   if (usage >= 1) {
//     characterColor = "#DC2626";
//   } else if (usage >= 0.9) {
//     characterColor = "#F59E0B";
//   }
//   return (
//     <Box
//       sx={{
//         mt: 2,

//         display: "flex",
//         justifyContent: "space-between",
//         alignItems: "center",

//         flexWrap: "wrap",
//         gap: 2,
//       }}
//     >
//       <Typography
//         sx={{
//           ...TYPOGRAPHY.helperText,
//           color: characterColor,
//           fontWeight: 600,
//         }}
//       >
//         {characterCount} / {MAX_CHARACTERS} Characters
//       </Typography>

//       <Typography sx={TYPOGRAPHY.helperText}>Words: {wordCount}</Typography>

//       <Typography sx={TYPOGRAPHY.helperText}>
//         Reading Time: ~{readingTime}s
//       </Typography>
//     </Box>
//   );
// }
import { Box, Typography } from "@mui/material";

import { useFormContext } from "react-hook-form";

export default function CaptionStats() {
  const { watch } = useFormContext();

  const caption = watch("caption") || "";

  const MAX_CHARACTERS = 2200;

  const characterCount = caption.length;

  const wordCount = caption
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;

  const usage =
    characterCount / MAX_CHARACTERS;

  let characterColor = "text.secondary";

  if (usage >= 1) {
    characterColor = "error.main";
  } else if (usage >= 0.9) {
    characterColor = "warning.main";
  }

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "flex-end",
        alignItems: "center",
        gap: 2,
      }}
    >
      <Typography
        sx={{
          fontSize: 11.5,
          color: characterColor,
          fontWeight: 600,
        }}
      >
        {characterCount} / {MAX_CHARACTERS}
      </Typography>

      <Typography
        sx={{
          fontSize: 11.5,
          color: "text.secondary",
        }}
      >
        {wordCount} words
      </Typography>
    </Box>
  );
}