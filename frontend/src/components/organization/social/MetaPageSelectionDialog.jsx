import {
  Alert,
  Avatar,
  Box,
  Button,
  CircularProgress,
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

import { useEffect, useState } from "react";

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
      aria-labelledby="facebook-page-selection-dialog-title"
    >
      <DialogTitle id="facebook-page-selection-dialog-title">
        Select a Facebook Page
      </DialogTitle>

      <DialogContent dividers>
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
          <Box
            sx={{
              minHeight: 180,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <CircularProgress size={30} />
          </Box>
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
                    borderColor: isSelected ? "primary.main" : "divider",
                    borderRadius: "12px",
                    alignItems: "flex-start",
                    px: 2,
                    py: 1.5,
                    transition: "border-color 0.2s ease",
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

      <DialogActions
        sx={{
          px: 3,
          py: 2,
        }}
      >
        <Button onClick={onClose} disabled={submitting}>
          Cancel
        </Button>

        <Button
          variant="contained"
          onClick={handleConfirm}
          disabled={loading || submitting || !selectedPageId}
          startIcon={
            submitting ? <CircularProgress size={18} color="inherit" /> : null
          }
        >
          {submitting ? "Connecting..." : "Connect Page"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
