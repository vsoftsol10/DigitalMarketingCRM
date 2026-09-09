import { Box, Divider } from "@mui/material";

import PreviewMedia from "./PreviewMedia";
import PreviewHeader from "./PreviewHeader";
import PreviewActions from "./PreviewActions";
import PreviewCaption from "./PreviewCaption";

export default function PreviewPostCard({
  organization,
  platform,
  accounts = [],
  contentType = "",
  caption = "",
  media = [],
}) {
  return (
    <Box
      sx={{
        maxWidth: 420,

        mx: "auto",

        border: "1px solid #E2E8F0",

        borderRadius: "22px",

        bgcolor: "#FFFFFF",

        overflow: "hidden",
      }}
    >
      {/* =====================================================
          HEADER
      ===================================================== */}

      <PreviewHeader
        organization={organization}
        platform={platform}
        accounts={accounts}
      />

      <Divider />

      {/* =====================================================
          MEDIA
      ===================================================== */}

      <PreviewMedia
        media={Array.isArray(media) ? media : []}
        platform={platform?.id || ""}
        contentType={contentType}
      />

      {/* =====================================================
          ACTIONS
      ===================================================== */}

      <PreviewActions />

      {/* =====================================================
          CAPTION
      ===================================================== */}

      <PreviewCaption caption={caption} />
    </Box>
  );
}
