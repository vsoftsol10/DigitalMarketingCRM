import { Box, Typography } from "@mui/material";

import MediaPreviewItem from "./MediaPreviewItem";

export default function MediaPreviewGrid({ media = [], onRemove }) {
  if (!media.length) {
    return null;
  }

  return (
    <Box>
      {/* =====================================================
          HEADER
      ===================================================== */}

      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",

          mb: 1.5,
        }}
      >
        <Typography
          sx={{
            fontSize: 13,
            fontWeight: 600,
            color: "text.primary",
          }}
        >
          Uploaded Media
        </Typography>

        <Typography
          sx={{
            fontSize: 12,
            color: "text.secondary",
          }}
        >
          {media.length} {media.length === 1 ? "file" : "files"}
        </Typography>
      </Box>

      {/* =====================================================
          MEDIA GRID
      ===================================================== */}

      <Box
        sx={{
          display: "grid",

          gridTemplateColumns: {
            xs: "repeat(2, minmax(0, 1fr))",
            sm: "repeat(3, minmax(0, 1fr))",
            md: "repeat(4, minmax(0, 1fr))",
          },

          gap: 1.5,
        }}
      >
        {media.map((item, index) => (
          <MediaPreviewItem
            key={item.id}
            media={item}
            index={index}
            onRemove={onRemove}
          />
        ))}
      </Box>
    </Box>
  );
}
