import { Avatar, Box, Divider, Stack, Typography } from "@mui/material";
import FavoriteBorderRoundedIcon from "@mui/icons-material/FavoriteBorderRounded";
import ChatBubbleOutlineRoundedIcon from "@mui/icons-material/ChatBubbleOutlineRounded";
import SendRoundedIcon from "@mui/icons-material/SendRounded";
import BookmarkBorderRoundedIcon from "@mui/icons-material/BookmarkBorderRounded";
import { TYPOGRAPHY } from "../../../../theme/typography";
import PreviewMedia from "./PreviewMedia";
import PreviewHeader from "./PreviewHeader";
import PreviewActions from "./PreviewActions";
import PreviewCaption from "./PreviewCaption";

export default function PreviewPostCard({
  organization,
  caption,
  media,
  platform,
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
      {/* Header */}

      <PreviewHeader organization={organization} platform={platform} />

      <Divider />

      {/* Media */}

      <PreviewMedia media={media} />

      {/* Actions */}

      <PreviewActions />

      {/* Caption */}

      <PreviewCaption caption={caption} />
    </Box>
  );
}
