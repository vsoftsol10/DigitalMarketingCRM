import {
  Alert,
  Avatar,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  List,
  ListItem,
  ListItemText,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import LoadingState from "../../ui/LoadingState";

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
  addingPageId = "",
  finishing = false,
  pageErrors = {},
  error = "",
  sessionInvalid = false,
  onDismiss,
  onFinish,
  onReconnect,
  onAdd,
}) {
  const busy = Boolean(loading || addingPageId || finishing);

  return (
    <Dialog
      open={open}
      onClose={() => {
        if (!busy) {
          onDismiss();
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
          Add the Facebook Pages you want connected to this organization. You can
          add more Pages here without authorizing Facebook again.
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
          <Alert severity="info">
            No eligible Facebook Pages were found. Check that your Facebook
            account has access to a Page, then connect Facebook again to refresh
            the available Pages.
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
              const isConnected = Boolean(page?.connected);
              const isAdding = addingPageId === pageId;
              const pageError = pageErrors[pageId];

              return (
                <ListItem
                  key={pageId}
                  sx={{
                    border: "1px solid",
                    borderColor: isConnected ? "rgba(58,142,98,.45)" : "rgba(202,220,248,.84)",
                    borderRadius: "15px",
                    alignItems: "center",
                    gap: 1.5,
                    px: { xs: 1.25, sm: 2 },
                    py: 1.5,
                    background: "linear-gradient(145deg, rgba(255,255,255,.9), rgba(238,245,255,.76))",
                    boxShadow: "0 3px 8px rgba(73,99,153,.05), inset 0 1px 0 #fff",
                    flexWrap: { xs: "wrap", sm: "nowrap" },
                  }}
                >
                  <Avatar
                    src={page?.profile_image || undefined}
                    alt={pageName}
                    sx={{
                      width: 42,
                      height: 42,
                    }}
                  >
                    {pageName.charAt(0).toUpperCase()}
                  </Avatar>

                  <ListItemText
                    sx={{ minWidth: 0, flex: 1 }}
                    primary={
                      <Typography variant="subtitle1" fontWeight={600}>
                        {pageName}
                      </Typography>
                    }
                    secondary={`Facebook Page ID: ${pageId}`}
                  />
                  <Button
                    variant={isConnected ? "outlined" : "contained"}
                    startIcon={isAdding ? <CircularProgress size={16} color="inherit" /> : isConnected ? undefined : <AddIcon />}
                    disabled={busy || isConnected || !pageId}
                    onClick={() => onAdd(pageId)}
                    aria-label={
                      isConnected
                        ? `${pageName} is connected`
                        : isAdding
                          ? `Adding ${pageName}`
                          : `Add ${pageName}`
                    }
                    sx={{
                      minWidth: { xs: "100%", sm: 112 },
                      ml: { xs: 0, sm: 1 },
                      ...(!isConnected ? glassPrimaryButtonSx : {}),
                    }}
                  >
                    {isConnected ? "Connected" : isAdding ? "Adding..." : "+ Add"}
                  </Button>
                  {pageError && (
                    <Alert severity="error" role="alert" sx={{ width: "100%", mt: 0.5 }}>
                      {pageError}
                    </Alert>
                  )}
                </ListItem>
              );
            })}
          </List>
        )}
      </DialogContent>

      <DialogActions sx={glassDialogActionsSx}>
        {(error || (!loading && pages.length === 0)) && (
          <Button onClick={onReconnect} disabled={busy}>
            Connect Facebook again
          </Button>
        )}
        <Button
          onClick={onDismiss}
          disabled={busy}
          aria-label="Close Facebook Page selection"
          sx={glassDialogSecondaryButtonSx}
        >
          Close
        </Button>
        <Button
          onClick={onFinish}
          disabled={busy || sessionInvalid}
          sx={{ minWidth: 150, ...glassDialogSecondaryButtonSx }}
        >
          {finishing ? "Finishing..." : "I'm done adding"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
