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
  ListItem,
  ListItemText,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LoadingState from "../../ui/LoadingState";
import LoadingSpinner from "../../ui/LoadingSpinner";

import {
  socialDialogActionsSx,
  socialDialogFacebookIconTileSx,
  socialDialogPaperSx,
  socialDialogPrimaryButtonSx,
  socialDialogSecondaryButtonSx,
  socialDialogTitleSx,
  socialDialogContentSx,
  socialPageConnectedButtonSx,
  socialPageRowSx,
} from "./socialDialogUiSx";

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
      PaperProps={{ sx: socialDialogPaperSx }}
      aria-labelledby="facebook-page-selection-dialog-title"
    >
      <DialogTitle id="facebook-page-selection-dialog-title" sx={socialDialogTitleSx}>
        <Box aria-hidden="true" sx={socialDialogFacebookIconTileSx}>
          <FacebookRoundedIcon />
        </Box>
        <Typography component="span" sx={{ minWidth: 0, overflowWrap: "anywhere" }}>
          Select a Facebook Page
        </Typography>
      </DialogTitle>

      <DialogContent dividers sx={socialDialogContentSx}>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: 2.25,
            color: "#64748B",
            lineHeight: 1.55,
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
            sx={{ py: 1 }}
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
              gap: 1.25,
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
                  sx={socialPageRowSx(isConnected)}
                >
                  <Avatar
                    src={page?.profile_image || undefined}
                    alt={pageName}
                    sx={{
                      width: 42,
                      height: 42,
                      flex: "0 0 auto",
                      bgcolor: "#EFF6FF",
                      color: "#1877F2",
                      border: "1px solid #D7E7FF",
                    }}
                  >
                    {pageName.charAt(0).toUpperCase()}
                  </Avatar>

                  <ListItemText
                    sx={{ minWidth: 0, flex: 1 }}
                    primary={
                      <Typography variant="subtitle1" fontWeight={600} sx={{ color: "#172554", overflowWrap: "anywhere" }}>
                        {pageName}
                      </Typography>
                    }
                    secondary={<Typography component="span" sx={{ color: "#64748B", fontSize: 12, lineHeight: 1.45, overflowWrap: "anywhere" }}>{`Facebook Page ID: ${pageId}`}</Typography>}
                  />
                  <Button
                    variant={isConnected ? "outlined" : "contained"}
                    startIcon={isAdding ? <LoadingSpinner size={16} color="inherit" decorative /> : isConnected ? undefined : <AddIcon />}
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
                      ...(isConnected ? socialPageConnectedButtonSx : socialDialogPrimaryButtonSx),
                    }}
                  >
                    {isConnected ? "Connected" : isAdding ? "Adding..." : "+ Add"}
                  </Button>
                  {pageError && (
                    <Alert severity="error" role="alert" sx={{ width: "100%", mt: 0.5, borderRadius: "12px", boxShadow: "none" }}>
                      {pageError}
                    </Alert>
                  )}
                </ListItem>
              );
            })}
          </List>
        )}
      </DialogContent>

      <DialogActions sx={socialDialogActionsSx}>
        {(error || (!loading && pages.length === 0)) && (
          <Button variant="outlined" onClick={onReconnect} disabled={busy} sx={socialDialogSecondaryButtonSx}>
            Connect Facebook again
          </Button>
        )}
        <Button
          onClick={onDismiss}
          disabled={busy}
          aria-label="Close Facebook Page selection"
          sx={socialDialogSecondaryButtonSx}
        >
          Close
        </Button>
        <Button
          onClick={onFinish}
          disabled={busy || sessionInvalid}
          sx={{ minWidth: { sm: 150 }, ...socialDialogSecondaryButtonSx }}
        >
          {finishing ? "Finishing..." : "I'm done adding"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
