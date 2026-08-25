import { Grid } from "@mui/material";

import SectionCard from "../SectionCard";

import AIPromptField from "./AIPromptField";
import AIToneSelect from "./AIToneSelect";
import AILengthSelect from "./AILengthSelect";
import AIContentOptions from "./AIContentOptions";
import AIGenerateButton from "./AIGenerateButton";
import AISuggestions from "./AISuggestions";
import { useState } from "react";
export default function AICaptionSection() {
  const [suggestions, setSuggestions] = useState([]);
  return (
    <SectionCard
      title="AI Caption Assistant"
      description="Generate engaging captions using AI based on your content and preferences."
    >
      <Grid container spacing={3}>
        <Grid size={12}>
          <AIPromptField />
        </Grid>

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

        <Grid size={12}>
          <AIContentOptions />
        </Grid>

        <Grid size={12}>
          <AIGenerateButton setSuggestions={setSuggestions} />
        </Grid>

        <Grid size={12}>
          <AISuggestions suggestions={suggestions} />
        </Grid>
      </Grid>
    </SectionCard>
  );
}
