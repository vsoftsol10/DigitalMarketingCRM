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
import {
  glassDialogActionsSx as organizationDialogActionsSx,
  glassDialogContentSx as organizationDialogContentSx,
  glassDialogDangerButtonSx as organizationDialogDangerButtonSx,
  glassDialogPaperSx as organizationDialogPaperSx,
  glassDialogSecondaryButtonSx as organizationDialogSecondaryButtonSx,
  glassDialogTitleSx as organizationDialogTitleSx,
  organizationPrimaryButtonSx,
} from "../../organization/organizationUiSx";
import {
  plannerDialogActionsSx,
  plannerDialogContentSx,
  plannerDialogDangerButtonSx,
  plannerDialogPaperSx,
  plannerDialogSecondaryButtonSx,
  plannerDialogTitleSx,
  plannerPrimaryButtonSx,
} from "../../planner/plannerUiSx";

const crmDialogPaperSx = {
  border: "1px solid #E2E8F0",
  borderRadius: "18px",
  background: "#FFFFFF",
  boxShadow: "0 16px 40px rgba(30, 45, 85, 0.16)",
};

const crmDialogTitleSx = {
  px: 3,
  py: 2.25,
  color: "#17294D",
  fontSize: "1.125rem",
  lineHeight: 1.4,
  fontWeight: 700,
  background: "#FFFFFF",
};

const crmDialogContentSx = {
  px: 3,
  py: 2.5,
  background: "#FFFFFF",
};

const crmDialogActionsSx = {
  px: 3,
  py: 2,
  gap: 1,
  flexWrap: "wrap",
  background: "#FFFFFF",
};

const crmSecondaryButtonSx = {
  minWidth: 100,
  minHeight: 42,
  height: "auto",
  borderRadius: "11px",
  borderColor: "#D7DFEC",
  color: "#405778",
  background: "#FFFFFF",
  boxShadow: "none",
  textTransform: "none",
  "&:hover": {
    borderColor: "#B8C7E7",
    background: "#F8FAFF",
    boxShadow: "none",
  },
};

const crmPrimaryButtonSx = {
  minWidth: 100,
  minHeight: 42,
  height: "auto",
  borderRadius: "11px",
  color: "#FFFFFF",
  background: "linear-gradient(105deg, #8757F3 0%, #625FF1 55%, #3689EC 100%)",
  boxShadow: "0 6px 14px rgba(92, 91, 219, 0.18)",
  textTransform: "none",
  "&:hover": {
    background: "linear-gradient(105deg, #7948EA 0%, #5452E8 55%, #2879DF 100%)",
    boxShadow: "0 8px 18px rgba(92, 91, 219, 0.22)",
  },
  "&.Mui-disabled": {
    color: "#FFFFFF",
    background: "#B8B9CB",
    boxShadow: "none",
  },
};

const crmDangerButtonSx = {
  ...crmPrimaryButtonSx,
  background: "#D9475C",
  boxShadow: "0 5px 12px rgba(190, 55, 75, 0.14)",
  "&:hover": {
    background: "#C9364B",
    boxShadow: "0 7px 16px rgba(190, 55, 75, 0.2)",
  },
  "&.Mui-disabled": {
    color: "#FFFFFF",
    background: "#D9A0A8",
    boxShadow: "none",
  },
};

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
  crmStyle = false,
  organizationStyle = false,
  plannerStyle = false,
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
          ...(organizationStyle && organizationDialogPaperSx),
          ...(plannerStyle && plannerDialogPaperSx),
          ...(crmStyle && crmDialogPaperSx),
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
          ...(organizationStyle && organizationDialogTitleSx),
          ...(plannerStyle && plannerDialogTitleSx),
          ...(crmStyle && crmDialogTitleSx),
        }}
      >
        {title}

        <IconButton onClick={onClose} size="small">
          <CloseRoundedIcon />
        </IconButton>
      </DialogTitle>

      <Divider sx={crmStyle ? { borderColor: "#E8ECF3" } : glass ? { borderColor: "rgba(146,168,201,.22)" } : plannerStyle ? { borderColor: "#E5E9F1" } : undefined} />

      {/* Body */}

      <DialogContent
        sx={{
          px: 3,
          py: 3,
          ...(glass && glassDialogContentSx),
          ...(organizationStyle && organizationDialogContentSx),
          ...(plannerStyle && plannerDialogContentSx),
          ...(crmStyle && crmDialogContentSx),
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

      <Divider sx={crmStyle ? { borderColor: "#E8ECF3" } : glass ? { borderColor: "rgba(146,168,201,.22)" } : plannerStyle ? { borderColor: "#E5E9F1" } : undefined} />

      {/* Footer */}

      <DialogActions
        sx={{
          px: 3,
          py: 3,
          ...(glass && glassDialogActionsSx),
          ...(organizationStyle && organizationDialogActionsSx),
          ...(plannerStyle && plannerDialogActionsSx),
          ...(crmStyle && crmDialogActionsSx),
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
            ...(organizationStyle && organizationDialogSecondaryButtonSx),
            ...(plannerStyle && plannerDialogSecondaryButtonSx),
            ...(crmStyle && crmSecondaryButtonSx),
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
            ...(organizationStyle && (destructive ? organizationDialogDangerButtonSx : organizationPrimaryButtonSx)),
            ...(plannerStyle && (destructive ? plannerDialogDangerButtonSx : plannerPrimaryButtonSx)),
            ...(crmStyle && (destructive ? crmDangerButtonSx : crmPrimaryButtonSx)),

            "&:hover": {
              ...(glass && !destructive
                ? glassPrimaryButtonSx["&:hover"]
                : {
                    boxShadow: glass
                      ? "0 8px 18px rgba(176,54,79,.25), inset 0 1px 0 rgba(255,255,255,.36)"
                      : "none",
                  }),
              ...(plannerStyle
                ? destructive
                  ? { background: "#C93248", boxShadow: "none" }
                  : plannerPrimaryButtonSx["&:hover"]
                : {}),
              ...(crmStyle
                ? destructive
                  ? crmDangerButtonSx["&:hover"]
                  : crmPrimaryButtonSx["&:hover"]
                : {}),
            },
          }}
        >
          {confirmText}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
