import { Paper, Box, Typography } from "@mui/material";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function SectionCard({
  title,
  description,
  children,
  compact = false,
}) {
  return (
    <Paper
      elevation={0}
      sx={{
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 3,
        bgcolor: "background.paper",
        p: compact ? 2.5 : 4,
      }}
    >
      <Box
        sx={{
          mb: compact ? 2 : 3,
        }}
      >
        <Typography sx={TYPOGRAPHY.sectionTitle}>
          {title}
        </Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.sectionDescription,
            mt: 0.25,
          }}
        >
          {description}
        </Typography>
      </Box>

      {children}
    </Paper>
  );
}