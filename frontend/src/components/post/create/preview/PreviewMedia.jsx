import { Box, Typography } from "@mui/material";
import ImageOutlinedIcon from "@mui/icons-material/ImageOutlined";
import VideocamOutlinedIcon from "@mui/icons-material/VideocamOutlined";

import { TYPOGRAPHY } from "../../../../theme/typography";

export default function PreviewMedia({
  media = [],
}) {
  if (!media.length) {
    return (
      <Box
        sx={{
          height: 320,
          bgcolor: "#F8FAFC",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 1,
        }}
      >
        <ImageOutlinedIcon
          sx={{
            fontSize: 42,
            color: "#94A3B8",
          }}
        />

        <Typography sx={TYPOGRAPHY.bodySmall}>
          Upload media to preview
        </Typography>
      </Box>
    );
  }

  const firstMedia = media[0];

  if (firstMedia.type === "VIDEO") {
    return (
      <Box
        component="video"
        controls
        src={firstMedia.preview}
        sx={{
          width: "100%",
          height: 320,
          objectFit: "cover",
          bgcolor: "#000",
        }}
      />
    );
  }

  return (
    <Box
      component="img"
      src={firstMedia.preview}
      alt={firstMedia.name}
      sx={{
        width: "100%",
        height: 320,
        objectFit: "cover",
      }}
    />
  );
}