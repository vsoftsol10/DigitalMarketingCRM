import { Box, Typography } from "@mui/material";

import { TYPOGRAPHY } from "../../../../theme/typography";

export default function PreviewCaption({ caption }) {
  return (
    <Box
      sx={{
        px: 2,
        pb: 2,
      }}
    >
      <Typography
        sx={{
          ...TYPOGRAPHY.body,
          color: "#334155",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {caption || "Your caption will appear here..."}
      </Typography>
    </Box>
  );
}
