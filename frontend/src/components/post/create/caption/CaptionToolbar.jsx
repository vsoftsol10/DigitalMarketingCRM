import {
  Box,
  Divider,
  IconButton,
  Tooltip,
} from "@mui/material";

import { useFormContext } from "react-hook-form";

import toast from "react-hot-toast";

import InsertEmoticonOutlinedIcon from "@mui/icons-material/InsertEmoticonOutlined";
import TagOutlinedIcon from "@mui/icons-material/TagOutlined";
import AlternateEmailOutlinedIcon from "@mui/icons-material/AlternateEmailOutlined";
import ContentCopyOutlinedIcon from "@mui/icons-material/ContentCopyOutlined";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";

export default function CaptionToolbar() {
  const { watch, setValue } = useFormContext();

  const caption = watch("caption") || "";

  async function handleCopy() {
    if (!caption.trim()) {
      toast.error("Caption is empty");
      return;
    }

    await navigator.clipboard.writeText(caption);

    toast.success("Caption copied");
  }

  function handleClear() {
    setValue("caption", "", {
      shouldDirty: true,
      shouldValidate: true,
    });

    toast.success("Caption cleared");
  }

  return (
    <Box
      sx={{
        mt: 2,

        px: 1,

        height: 48,

        display: "flex",
        alignItems: "center",
        gap: 0.5,

        border: "1px solid #E2E8F0",
        borderRadius: "14px",

        bgcolor: "#F8FAFC",
      }}
    >
      <Tooltip title="Emoji">
        <IconButton size="small">
          <InsertEmoticonOutlinedIcon fontSize="small" />
        </IconButton>
      </Tooltip>

      <Tooltip title="Hashtag">
        <IconButton size="small">
          <TagOutlinedIcon fontSize="small" />
        </IconButton>
      </Tooltip>

      <Tooltip title="Mention">
        <IconButton size="small">
          <AlternateEmailOutlinedIcon fontSize="small" />
        </IconButton>
      </Tooltip>

      <Divider
        orientation="vertical"
        flexItem
        sx={{
          mx: 1,
        }}
      />

      <Tooltip title="Copy Caption">
        <IconButton
          size="small"
          onClick={handleCopy}
        >
          <ContentCopyOutlinedIcon fontSize="small" />
        </IconButton>
      </Tooltip>

      <Tooltip title="Clear Caption">
        <IconButton
          size="small"
          onClick={handleClear}
        >
          <DeleteOutlineOutlinedIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </Box>
  );
}