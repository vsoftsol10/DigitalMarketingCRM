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
import { glassPrimaryButtonSx } from "../form/glassFormSx";
import {
  glassDialogActionsSx,
  glassDialogContentSx,
  glassDialogDangerButtonSx,
  glassDialogPaperSx,
  glassDialogSecondaryButtonSx,
  glassDialogTitleSx,
} from "./glassDialogSx";

export default function ConfirmDialog({
  open,
  title,
  message,
  entityName,
  description,
  confirmText = "Delete",
  cancelText = "Cancel",
  loading = false,
  glass = false,
  destructive = true,
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
          ...(glass && glassDialogPaperSx),
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
          ...(glass && {
            ...glassDialogTitleSx,
            borderBottom: "none",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }),
        }}
      >
        {title}

        <IconButton onClick={onClose} size="small">
          <CloseRoundedIcon />
        </IconButton>
      </DialogTitle>

      <Divider sx={glass ? { borderColor: "rgba(146,168,201,.22)" } : undefined} />

      {/* Body */}

      <DialogContent
        sx={{
          px: 3,
          py: 3,
          ...(glass && glassDialogContentSx),
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

      <Divider sx={glass ? { borderColor: "rgba(146,168,201,.22)" } : undefined} />

      {/* Footer */}

      <DialogActions
        sx={{
          px: 3,
          py: 3,
          ...(glass && glassDialogActionsSx),
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
            ...(glass && glassDialogSecondaryButtonSx),
          }}
        >
          {cancelText}
        </Button>

        <Button
          variant="contained"
          color={destructive ? "error" : "primary"}
          onClick={onConfirm}
          disabled={loading}
          sx={{
            minWidth: 100,
            height: 48,
            borderRadius: "16px",
            textTransform: "none",

            boxShadow: "none",

            ...TYPOGRAPHY.formButton,
            ...(glass && (destructive ? glassDialogDangerButtonSx : glassPrimaryButtonSx)),

            "&:hover": {
              ...(glass && !destructive
                ? glassPrimaryButtonSx["&:hover"]
                : {
                    boxShadow: glass
                      ? "0 8px 18px rgba(176,54,79,.25), inset 0 1px 0 rgba(255,255,255,.36)"
                      : "none",
                  }),
            },
          }}
        >
          {confirmText}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
