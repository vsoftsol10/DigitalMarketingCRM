import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  Typography,
} from "@mui/material";

import CloseRoundedIcon from "@mui/icons-material/CloseRounded";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function ConfirmDialog({
  open,
  title,
  message,
  entityName,
  description,
  confirmText = "Delete",
  cancelText = "Cancel",
  loading = false,
  onClose,
  onConfirm,
}) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: "24px",
          overflow: "hidden",
        },
      }}
    >
      {/* Header */}

      <DialogTitle
        sx={{
          px: 3,
          py: 2.5,

          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",

          ...TYPOGRAPHY.sectionTitle,
        }}
      >
        {title}

        <IconButton onClick={onClose} size="small">
          <CloseRoundedIcon />
        </IconButton>
      </DialogTitle>

      <Divider />

      {/* Body */}

      <DialogContent
        sx={{
          px: 3,
          py: 3,
        }}
      >
        <Typography
          sx={{
            ...TYPOGRAPHY.body,
            color: "#475569",
            lineHeight: 1.8,
          }}
        >
          {message}{" "}
          <Typography
            component="span"
            sx={{
              fontWeight: 700,
              color: "#1E293B",
            }}
          >
            {entityName}
          </Typography>
          ? {description}
        </Typography>
      </DialogContent>

      <Divider />

      {/* Footer */}

      <DialogActions
        sx={{
          px: 3,
          py: 3,
        }}
      >
        <Button
          variant="outlined"
          onClick={onClose}
          sx={{
            minWidth: 100,
            height: 48,
            borderRadius: "16px",
            textTransform: "none",

            borderColor: "#CBD5E1",

            color: "#334155",

            ...TYPOGRAPHY.formButton,
          }}
        >
          {cancelText}
        </Button>

        <Button
          variant="contained"
          color="error"
          onClick={onConfirm}
          disabled={loading}
          sx={{
            minWidth: 100,
            height: 48,
            borderRadius: "16px",
            textTransform: "none",

            boxShadow: "none",

            ...TYPOGRAPHY.formButton,

            "&:hover": {
              boxShadow: "none",
            },
          }}
        >
          {confirmText}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
