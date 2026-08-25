import { Box, TextField, Typography } from "@mui/material";

import { Controller, useFormContext } from "react-hook-form";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function PlanHighlightsForm() {
  const { control } = useFormContext();

  return (
    <Box>
      <Typography sx={TYPOGRAPHY.sectionTitle}>Plan Highlights</Typography>

      <Typography
        sx={{
          ...TYPOGRAPHY.sectionDescription,
          mt: 0.25,
          mb: 3,
        }}
      >
        A short description of what this plan is best for.
      </Typography>

      <Controller
        name="highlights"
        control={control}
        render={({ field }) => (
          <TextField
            {...field}
            fullWidth
            multiline
            minRows={3}
            placeholder="Add a short description of what this plan is best for..."
          />
        )}
      />
    </Box>
  );
}
