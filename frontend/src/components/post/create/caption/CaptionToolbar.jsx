// import {
//   Box,
//   Divider,
//   IconButton,
//   Tooltip,
// } from "@mui/material";

// import { useFormContext } from "react-hook-form";

// import toast from "react-hot-toast";

// import InsertEmoticonOutlinedIcon from "@mui/icons-material/InsertEmoticonOutlined";
// import TagOutlinedIcon from "@mui/icons-material/TagOutlined";
// import AlternateEmailOutlinedIcon from "@mui/icons-material/AlternateEmailOutlined";
// import ContentCopyOutlinedIcon from "@mui/icons-material/ContentCopyOutlined";
// import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";

// export default function CaptionToolbar() {
//   const { watch, setValue } = useFormContext();

//   const caption = watch("caption") || "";

//   async function handleCopy() {
//     if (!caption.trim()) {
//       toast.error("Caption is empty");
//       return;
//     }

//     await navigator.clipboard.writeText(caption);

//     toast.success("Caption copied");
//   }

//   function handleClear() {
//     setValue("caption", "", {
//       shouldDirty: true,
//       shouldValidate: true,
//     });

//     toast.success("Caption cleared");
//   }

//   return (
//     <Box
//       sx={{
//         mt: 2,

//         px: 1,

//         height: 48,

//         display: "flex",
//         alignItems: "center",
//         gap: 0.5,

//         border: "1px solid #E2E8F0",
//         borderRadius: "14px",

//         bgcolor: "#F8FAFC",
//       }}
//     >
//       <Tooltip title="Emoji">
//         <IconButton size="small">
//           <InsertEmoticonOutlinedIcon fontSize="small" />
//         </IconButton>
//       </Tooltip>

//       <Tooltip title="Hashtag">
//         <IconButton size="small">
//           <TagOutlinedIcon fontSize="small" />
//         </IconButton>
//       </Tooltip>

//       <Tooltip title="Mention">
//         <IconButton size="small">
//           <AlternateEmailOutlinedIcon fontSize="small" />
//         </IconButton>
//       </Tooltip>

//       <Divider
//         orientation="vertical"
//         flexItem
//         sx={{
//           mx: 1,
//         }}
//       />

//       <Tooltip title="Copy Caption">
//         <IconButton
//           size="small"
//           onClick={handleCopy}
//         >
//           <ContentCopyOutlinedIcon fontSize="small" />
//         </IconButton>
//       </Tooltip>

//       <Tooltip title="Clear Caption">
//         <IconButton
//           size="small"
//           onClick={handleClear}
//         >
//           <DeleteOutlineOutlinedIcon fontSize="small" />
//         </IconButton>
//       </Tooltip>
//     </Box>
//   );
// }
import {
  Box,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  Tooltip,
} from "@mui/material";

import { useState } from "react";
import { useFormContext } from "react-hook-form";

import toast from "react-hot-toast";

import InsertEmoticonOutlinedIcon from "@mui/icons-material/InsertEmoticonOutlined";
import TagOutlinedIcon from "@mui/icons-material/TagOutlined";
import AlternateEmailOutlinedIcon from "@mui/icons-material/AlternateEmailOutlined";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";

const EMOJIS = [
  "😀",
  "😊",
  "😍",
  "🔥",
  "✨",
  "❤️",
  "👏",
  "🎉",
  "🚀",
  "💡",
  "☕",
  "📢",
];

export default function CaptionToolbar() {
  const { watch, setValue } = useFormContext();

  const caption = watch("caption") || "";

  const [emojiAnchor, setEmojiAnchor] =
    useState(null);

  function updateCaption(value) {
    setValue("caption", value, {
      shouldDirty: true,
      shouldValidate: true,
    });
  }

  function appendToCaption(value) {
    const current = caption.trimEnd();

    const separator =
      current.length > 0 ? " " : "";

    updateCaption(
      `${current}${separator}${value}`,
    );
  }

  function handleEmojiOpen(event) {
    setEmojiAnchor(event.currentTarget);
  }

  function handleEmojiClose() {
    setEmojiAnchor(null);
  }

  function handleEmojiSelect(emoji) {
    appendToCaption(emoji);
    handleEmojiClose();
  }

  function handleHashtag() {
    appendToCaption("#");
  }

  function handleMention() {
    appendToCaption("@");
  }

  function handleClear() {
    updateCaption("");

    toast.success("Caption cleared");
  }

  return (
    <>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          width: "fit-content",
          minHeight: 38,
          px: 0.5,
          border: "1px solid",
          borderColor: "divider",
          borderRadius: "10px",
          bgcolor: "background.paper",
        }}
      >
        {/* Emoji */}
        <Tooltip title="Add emoji">
          <IconButton
            size="small"
            onClick={handleEmojiOpen}
            aria-label="Add emoji"
          >
            <InsertEmoticonOutlinedIcon
              fontSize="small"
            />
          </IconButton>
        </Tooltip>

        {/* Hashtag */}
        <Tooltip title="Add hashtag">
          <IconButton
            size="small"
            onClick={handleHashtag}
            aria-label="Add hashtag"
          >
            <TagOutlinedIcon fontSize="small" />
          </IconButton>
        </Tooltip>

        {/* Mention */}
        <Tooltip title="Add mention">
          <IconButton
            size="small"
            onClick={handleMention}
            aria-label="Add mention"
          >
            <AlternateEmailOutlinedIcon
              fontSize="small"
            />
          </IconButton>
        </Tooltip>

        <Divider
          orientation="vertical"
          flexItem
          sx={{
            mx: 0.5,
            my: 0.75,
          }}
        />

        {/* Clear */}
        <Tooltip title="Clear caption">
          <IconButton
            size="small"
            onClick={handleClear}
            disabled={!caption}
            aria-label="Clear caption"
          >
            <DeleteOutlineOutlinedIcon
              fontSize="small"
            />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Emoji picker */}
      <Menu
        anchorEl={emojiAnchor}
        open={Boolean(emojiAnchor)}
        onClose={handleEmojiClose}
        slotProps={{
          paper: {
            sx: {
              mt: 0.75,
              p: 0.5,
              borderRadius: "12px",
            },
          },
        }}
      >
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns:
              "repeat(4, 1fr)",
            gap: 0.25,
            p: 0.5,
          }}
        >
          {EMOJIS.map((emoji) => (
            <MenuItem
              key={emoji}
              onClick={() =>
                handleEmojiSelect(emoji)
              }
              sx={{
                minWidth: 40,
                minHeight: 40,
                justifyContent: "center",
                borderRadius: "8px",
                fontSize: 20,
              }}
            >
              {emoji}
            </MenuItem>
          ))}
        </Box>
      </Menu>
    </>
  );
}