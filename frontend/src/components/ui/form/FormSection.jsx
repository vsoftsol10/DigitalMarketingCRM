import { Box, Stack, Typography } from "@mui/material";
import { TYPOGRAPHY } from "../../../theme/typography";

export default function FormSection({
  title,
  description,
  children,
}) {
  return (
    <Box>
      <Stack spacing={4}>
        <Stack spacing={0.5}>
          <Typography sx={TYPOGRAPHY.sectionTitle}>
            {title}
          </Typography>

          {description && (
            <Typography
              sx={TYPOGRAPHY.sectionDescription}
            >
              {description}
            </Typography>
          )}
        </Stack>

        {children}
      </Stack>
    </Box>
  );
}