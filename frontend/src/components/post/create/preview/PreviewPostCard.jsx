import { Box, Divider } from "@mui/material";

import PreviewMedia from "./PreviewMedia";
import PreviewHeader from "./PreviewHeader";
import PreviewActions from "./PreviewActions";
import PreviewCaption from "./PreviewCaption";
import overviewGlassCardSx from "../../../organization/overview/overviewGlassCardSx";

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

        ...overviewGlassCardSx,
        borderRadius: "20px",
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
