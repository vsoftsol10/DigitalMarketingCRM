// import { Grid } from "@mui/material";

// import SectionCard from "../SectionCard";

// import AIPromptField from "./AIPromptField";
// import AIToneSelect from "./AIToneSelect";
// import AILengthSelect from "./AILengthSelect";
// import AIContentOptions from "./AIContentOptions";
// import AIGenerateButton from "./AIGenerateButton";
// import AISuggestions from "./AISuggestions";
// import { useState } from "react";
// export default function AICaptionSection() {
//   const [suggestions, setSuggestions] = useState([]);
//   return (
//     <SectionCard
//       title="AI Caption Assistant"
//       description="Generate engaging captions using AI based on your content and preferences."
//     >
//       <Grid container spacing={3}>
//         <Grid size={12}>
//           <AIPromptField />
//         </Grid>

//         <Grid
//           size={{
//             xs: 12,
//             md: 6,
//           }}
//         >
//           <AIToneSelect />
//         </Grid>

//         <Grid
//           size={{
//             xs: 12,
//             md: 6,
//           }}
//         >
//           <AILengthSelect />
//         </Grid>

//         <Grid size={12}>
//           <AIContentOptions />
//         </Grid>

//         <Grid size={12}>
//           <AIGenerateButton setSuggestions={setSuggestions} />
//         </Grid>

//         <Grid size={12}>
//           <AISuggestions suggestions={suggestions} />
//         </Grid>
//       </Grid>
//     </SectionCard>
//   );
// }

import { Grid, Stack } from "@mui/material";
import { useState } from "react";

import SectionCard from "../SectionCard";

import AIPromptField from "./AIPromptField";
import AIToneSelect from "./AIToneSelect";
import AILengthSelect from "./AILengthSelect";
import AIContentOptions from "./AIContentOptions";
import AIGenerateButton from "./AIGenerateButton";
import AISuggestions from "./AISuggestions";

export default function AICaptionSection() {
  const [suggestions, setSuggestions] = useState([]);

  const hasSuggestion = suggestions.length > 0;

  return (
    <SectionCard
      title="AI Caption Assistant"
      description="Create a caption with AI based on your content and preferences."
    >
      <Stack spacing={2}>
        {/* Prompt */}
        <AIPromptField />

        {/* Tone + Length */}
        <Grid container spacing={1.5}>
          <Grid
            size={{
              xs: 12,
              md: 6,
            }}
          >
            <AIToneSelect />
          </Grid>

          <Grid
            size={{
              xs: 12,
              md: 6,
            }}
          >
            <AILengthSelect />
          </Grid>
        </Grid>

        {/* AI options */}
        <AIContentOptions />

        {/* Generate / Regenerate */}
        <AIGenerateButton
          setSuggestions={setSuggestions}
          hasSuggestion={hasSuggestion}
        />

        {/* Single AI result */}
        <AISuggestions suggestions={suggestions} />
      </Stack>
    </SectionCard>
  );
}