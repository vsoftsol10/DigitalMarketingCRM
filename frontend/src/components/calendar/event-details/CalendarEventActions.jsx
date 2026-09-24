import {
  Box,
  Button,
  IconButton,
  Stack,
  Tooltip,
  CircularProgress,
} from "@mui/material";

import ScheduleRoundedIcon from "@mui/icons-material/ScheduleRounded";
import PublishRoundedIcon from "@mui/icons-material/PublishRounded";
import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
import ReplayRoundedIcon from "@mui/icons-material/ReplayRounded";

import { TYPOGRAPHY } from "../../../theme/typography";

const buttonSx = {
  minHeight: 40,
  px: 2,
  borderRadius: 1.75,
  ...TYPOGRAPHY.button,
};

const secondaryButtonSx = {
  ...buttonSx,
  borderColor: "divider",
  color: "text.primary",
  "&:hover": {
    bgcolor: "action.hover",
    borderColor: "text.disabled",
  },
};

export default function CalendarEventActions({
  event,
  onReschedule,
  onPublishNow,
  onRetry,
  onDelete,
  loading = false,
  loadingAction = null,
}) {
  if (!event) {
    return null;
  }

  const status = event.status?.toUpperCase();
  const handleAction = (callback) => callback?.(event);

  if (["PUBLISHED", "UNRESOLVED"].includes(status)) {
    return null;
  }

  const canDelete = ["DRAFT", "SCHEDULED", "FAILED"].includes(status);

  return (
    <Box
      sx={{
        width: "100%",
        px: { xs: 2.5, sm: 3 },
        py: 1.5,
        borderTop: "1px solid",
        borderColor: "divider",
        bgcolor: "background.paper",
        flexShrink: 0,
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        spacing={1}
      >
        {/* Primary + secondary actions, grouped left */}

        <Stack
          direction="row"
          spacing={1}
          sx={{ flex: 1, minWidth: 0 }}
        >
          {status === "DRAFT" && (
            <>
              <Button
                variant="contained"
                disableElevation
                startIcon={loadingAction === "publish" ? <CircularProgress size={16} color="inherit" /> : <PublishRoundedIcon />}
                onClick={() =>
                  handleAction(onPublishNow)
                }
                disabled={loading}
                sx={buttonSx}
              >
                {loadingAction === "publish" ? "Publishing..." : "Publish now"}
              </Button>

              <Button
                variant="outlined"
                startIcon={<ScheduleRoundedIcon />}
                onClick={() =>
                  handleAction(onReschedule)
                }
                disabled={loading}
                sx={secondaryButtonSx}
              >
                Schedule
              </Button>
            </>
          )}

          {status === "SCHEDULED" && (
            <>
              <Button
                variant="contained"
                disableElevation
                startIcon={<ScheduleRoundedIcon />}
                onClick={() =>
                  handleAction(onReschedule)
                }
                disabled={loading}
                sx={buttonSx}
              >
                Reschedule
              </Button>

              <Button
                variant="outlined"
                startIcon={loadingAction === "publish" ? <CircularProgress size={16} color="inherit" /> : <PublishRoundedIcon />}
                onClick={() =>
                  handleAction(onPublishNow)
                }
                disabled={loading}
                sx={secondaryButtonSx}
              >
                {loadingAction === "publish" ? "Publishing..." : "Publish now"}
              </Button>
            </>
          )}

          {status === "FAILED" && (
            <Button
              variant="contained"
              disableElevation
              color="error"
              startIcon={loadingAction === "retry" ? <CircularProgress size={16} color="inherit" /> : <ReplayRoundedIcon />}
              onClick={() => handleAction(onRetry)}
              disabled={loading}
              sx={buttonSx}
            >
              {loadingAction === "retry" ? "Retrying..." : "Retry"}
            </Button>
          )}
        </Stack>

        {/* Quiet, icon-only delete — kept out of the primary
            action group so it can't be mis-tapped */}

        {canDelete && (
          <Tooltip title="Delete post">
            <IconButton
              aria-label="Delete post"
              onClick={() => handleAction(onDelete)}
              disabled={loading}
              sx={{
                width: 40,
                height: 40,
                flexShrink: 0,
                borderRadius: 1.75,
                border: "1px solid",
                borderColor: "divider",
                color: "text.secondary",
                "&:hover": {
                  bgcolor: "error.lighter",
                  borderColor: "error.light",
                  color: "error.dark",
                },
              }}
            >
              <DeleteOutlineRoundedIcon
                sx={{ fontSize: 19 }}
              />
            </IconButton>
          </Tooltip>
        )}
      </Stack>
    </Box>
  );
}
