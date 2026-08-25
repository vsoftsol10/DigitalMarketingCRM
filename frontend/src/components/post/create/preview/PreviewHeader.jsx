import {
  Avatar,
  Box,
  Stack,
  Typography,
} from "@mui/material";

import { TYPOGRAPHY } from "../../../../theme/typography";

export default function PreviewHeader({
  organization,
  platform,
}) {
  return (
    <Stack
      direction="row"
      spacing={1.5}
      alignItems="center"
      sx={{
        p: 2,
      }}
    >
      <Avatar
        sx={{
          width: 42,
          height: 42,
          bgcolor: "#2563EB",
        }}
      >
        {organization?.name?.charAt(0) || "O"}
      </Avatar>

      <Box flex={1}>
        <Typography
          sx={{
            ...TYPOGRAPHY.body,
            fontWeight: 600,
            color: "#0F172A",
          }}
        >
          {organization?.name || "Organization"}
        </Typography>

        <Typography sx={TYPOGRAPHY.caption}>
          {platform?.name || "Instagram"} • Just now
        </Typography>
      </Box>
    </Stack>
  );
}