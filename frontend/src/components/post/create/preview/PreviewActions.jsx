import {
  Box,
  Stack,
} from "@mui/material";

import FavoriteBorderRoundedIcon from "@mui/icons-material/FavoriteBorderRounded";
import ChatBubbleOutlineRoundedIcon from "@mui/icons-material/ChatBubbleOutlineRounded";
import SendRoundedIcon from "@mui/icons-material/SendRounded";
import BookmarkBorderRoundedIcon from "@mui/icons-material/BookmarkBorderRounded";

export default function PreviewActions() {
  return (
    <Stack
      direction="row"
      spacing={2}
      sx={{
        px: 2,
        py: 1.5,
        color: "#526887",
        borderTop: "1px solid rgba(255,255,255,.82)",
        background: "rgba(247,250,255,.58)",
      }}
    >
      <FavoriteBorderRoundedIcon fontSize="small" />

      <ChatBubbleOutlineRoundedIcon fontSize="small" />

      <SendRoundedIcon fontSize="small" />

      <Box flex={1} />

      <BookmarkBorderRoundedIcon fontSize="small" />
    </Stack>
  );
}
