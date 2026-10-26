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
          color: "#647D9F",
          border: "1px solid rgba(255,255,255,.82)",
          background:
            "linear-gradient(145deg, rgba(250,252,255,.94), rgba(231,240,255,.82))",
          boxShadow:
            "0 4px 10px rgba(75,96,151,.08), inset 0 1px 0 rgba(255,255,255,.96)",
          "&:hover": {
            color: "#355FBC",
            background: "rgba(226,237,255,.8)",
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
            border: "1px solid rgba(255,255,255,.92)",
            background:
              "linear-gradient(145deg, rgba(250,252,255,.98), rgba(235,243,255,.96))",
            boxShadow:
              "0 14px 30px rgba(75,96,151,.16), 0 3px 8px rgba(79,99,154,.08), inset 0 1px 0 rgba(255,255,255,.98)",
            "& .MuiMenuItem-root": {
              minHeight: 44,
              mx: 0.75,
              my: 0.25,
              borderRadius: "10px",
              color: "#304563",
              "&:hover": { background: "rgba(226,237,255,.68)" },
              "&.Mui-focusVisible": {
                outline: "2px solid rgba(111,145,211,.42)",
                outlineOffset: -2,
              },
            },
            "& .MuiMenuItem-root:last-of-type": {
              mb: 0.5,
            },
            "& .MuiListItemIcon-root": {
              color: "#647D9F",
              minWidth: 36,
            },
            "& .MuiDivider-root": {
              borderColor: "rgba(146,168,201,.24)",
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
