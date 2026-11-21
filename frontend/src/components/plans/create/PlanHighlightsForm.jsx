import { Box, TextField, Typography } from "@mui/material";

import { Controller, useFormContext } from "react-hook-form";

import { planInputSx } from "../plansGlassSx";

export default function PlanHighlightsForm() {
  const { control } = useFormContext();

  return (
    <Box>
      <Typography sx={{ fontSize: 18, lineHeight: "24px", fontWeight: 700, color: "#1E293B" }}>
        Plan Highlights
      </Typography>

      <Typography
        sx={{
          mt: 0.35,
          mb: 2,
          fontSize: 14,
          lineHeight: "21px",
          color: "#64748B",
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
            sx={planInputSx}
          />
        )}
      />
    </Box>
  );
}
