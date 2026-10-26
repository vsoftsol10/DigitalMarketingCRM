import {
  Alert,
  Avatar,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  List,
  ListItemButton,
  ListItemText,
  Radio,
  Typography,
} from "@mui/material";
import LoadingState from "../../ui/LoadingState";

import { useEffect, useState } from "react";
import { glassPrimaryButtonSx } from "../../ui/form/glassFormSx";
import {
  glassDialogActionsSx,
  glassDialogContentSx,
  glassDialogPaperSx,
  glassDialogSecondaryButtonSx,
  glassDialogTitleSx,
} from "../../ui/dialog/glassDialogSx";

export default function MetaPageSelectionDialog({
  open,
  pages = [],
  loading = false,
  submitting = false,
  error = "",
  onClose,
  onConfirm,
}) {
  const [selectedPageId, setSelectedPageId] = useState("");

  useEffect(() => {
    if (!open) {
      setSelectedPageId("");
    }
  }, [open]);

  const handleConfirm = async () => {
    if (!selectedPageId || submitting) {
      return;
    }

    await onConfirm(selectedPageId);
  };

  return (
    <Dialog
      open={open}
      onClose={() => {
        if (!submitting) {
          onClose();
        }
      }}
      fullWidth
      maxWidth="sm"
      PaperProps={{ sx: glassDialogPaperSx }}
      aria-labelledby="facebook-page-selection-dialog-title"
    >
      <DialogTitle id="facebook-page-selection-dialog-title" sx={glassDialogTitleSx}>
        Select a Facebook Page
      </DialogTitle>

      <DialogContent dividers sx={glassDialogContentSx}>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: 2,
          }}
        >
          Select the Facebook Page you want to connect. Instagram accounts are
          connected separately through the Instagram connection flow.
        </Typography>

        {loading && (
          <LoadingState
            label="LOADING FACEBOOK PAGES..."
            variant="container"
            minHeight={180}
          />
        )}

        {!loading && error && (
          <Alert
            severity="error"
            sx={{
              mb: 2,
            }}
          >
            {error}
          </Alert>
        )}

        {!loading && !error && pages.length === 0 && (
          <Alert severity="warning">
            No Facebook Pages are available for this Meta authorization.
          </Alert>
        )}

        {!loading && !error && pages.length > 0 && (
          <List
            disablePadding
            aria-label="Available Facebook Pages"
            sx={{
              display: "flex",
              flexDirection: "column",
              gap: 1,
            }}
          >
            {pages.map((page) => {
              const pageId = String(page?.id || "");
              const pageName = String(page?.name || pageId);
              const isSelected = selectedPageId === pageId;

              return (
                <ListItemButton
                  key={pageId}
                  selected={isSelected}
                  disabled={submitting}
                  onClick={() => setSelectedPageId(pageId)}
                  sx={{
                    border: "1px solid",
                    borderColor: isSelected ? "#7D96D4" : "rgba(202,220,248,.84)",
                    borderRadius: "15px",
                    alignItems: "flex-start",
                    px: 2,
                    py: 1.5,
                    background: isSelected
                      ? "linear-gradient(145deg, rgba(230,240,255,.95), rgba(255,255,255,.86))"
                      : "linear-gradient(145deg, rgba(255,255,255,.9), rgba(238,245,255,.76))",
                    boxShadow: isSelected
                      ? "0 5px 12px rgba(84,112,179,.12), inset 0 1px 0 #fff"
                      : "0 3px 8px rgba(73,99,153,.05), inset 0 1px 0 #fff",
                    transition: "border-color 0.2s ease, box-shadow 0.2s ease, background .2s ease",
                  }}
                >
                  <Radio
                    checked={isSelected}
                    value={pageId}
                    tabIndex={-1}
                    disableRipple
                    sx={{
                      mt: -0.25,
                    }}
                  />

                  <Avatar
                    src={page?.profile_image || undefined}
                    alt={pageName}
                    sx={{
                      width: 42,
                      height: 42,
                      mr: 1.5,
                    }}
                  >
                    {pageName.charAt(0).toUpperCase()}
                  </Avatar>

                  <ListItemText
                    primary={
                      <Typography variant="subtitle1" fontWeight={600}>
                        {pageName}
                      </Typography>
                    }
                    secondary={`Facebook Page ID: ${pageId}`}
                  />
                </ListItemButton>
              );
            })}
          </List>
        )}
      </DialogContent>

      <DialogActions sx={glassDialogActionsSx}>
        <Button onClick={onClose} disabled={submitting} sx={glassDialogSecondaryButtonSx}>
          Cancel
        </Button>

        <Button
          variant="contained"
          onClick={handleConfirm}
          disabled={loading || submitting || !selectedPageId}
          sx={{ minWidth: 150, ...glassPrimaryButtonSx }}
        >
          {submitting ? "Connecting..." : "Connect Page"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
