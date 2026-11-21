import { useState } from "react";

import {
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from "@mui/material";

import MoreVertRoundedIcon from "@mui/icons-material/MoreVertRounded";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
import PostAddRoundedIcon from "@mui/icons-material/PostAddRounded";

export default function ContentPlannerActionMenu({
  onEdit,
  onDelete,
  onCreatePost,
}) {
  const [anchorEl, setAnchorEl] = useState(null);

  const open = Boolean(anchorEl);

  function handleOpen(event) {
    setAnchorEl(event.currentTarget);
  }

  function handleClose() {
    setAnchorEl(null);
  }

  return (
    <>
      <IconButton
        onClick={handleOpen}
        size="small"
        sx={{
          color: "#64748B",
          border: "1px solid #DDE3F1",
          background: "#FFFFFF",
          boxShadow: "none",
          "&:hover": {
            color: "#6941D9",
            background: "#F5F2FF",
          },
          "&.Mui-focusVisible": {
            outline: "2px solid rgba(111,145,211,.5)",
            outlineOffset: 2,
          },
        }}
      >
        <MoreVertRoundedIcon fontSize="small" />
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            width: 220,
            borderRadius: "16px",
            mt: 1,
            border: "1px solid #DDE3F1",
            background: "#FFFFFF",
            boxShadow: "0 12px 28px rgba(31,41,80,.14)",
            "& .MuiMenuItem-root": {
              minHeight: 44,
              mx: 0.75,
              my: 0.25,
              borderRadius: "10px",
              color: "#334155",
              "&:hover": { background: "#F5F2FF" },
              "&.Mui-focusVisible": {
                outline: "2px solid rgba(111,145,211,.42)",
                outlineOffset: -2,
              },
            },
            "& .MuiMenuItem-root:last-of-type": {
              mb: 0.5,
            },
            "& .MuiListItemIcon-root": {
              color: "#71809A",
              minWidth: 36,
            },
            "& .MuiDivider-root": {
              borderColor: "#E5E9F1",
              my: 0.5,
            },
          },
        }}
      >
        <MenuItem
          onClick={() => {
            handleClose();
            onEdit?.();
          }}
        >
          <ListItemIcon>
            <EditOutlinedIcon fontSize="small" />
          </ListItemIcon>

          <ListItemText>Edit</ListItemText>
        </MenuItem>

        <MenuItem
          onClick={() => {
            handleClose();
            onDelete?.();
          }}
        >
          <ListItemIcon>
            <DeleteOutlineRoundedIcon fontSize="small" color="error" />
          </ListItemIcon>

          <ListItemText
            sx={{
              color: "#C43E57",
            }}
          >
            Delete
          </ListItemText>
        </MenuItem>

        <Divider />

        <MenuItem
          onClick={() => {
            handleClose();
            onCreatePost?.();
          }}
        >
          <ListItemIcon>
            <PostAddRoundedIcon fontSize="small" />
          </ListItemIcon>

          <ListItemText>Create Post</ListItemText>
        </MenuItem>
      </Menu>
    </>
  );
}
