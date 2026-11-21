import {
  Box,
  Button,
  IconButton,
  Stack,
  Tooltip,
} from "@mui/material";

import ScheduleRoundedIcon from "@mui/icons-material/ScheduleRounded";
import PublishRoundedIcon from "@mui/icons-material/PublishRounded";
import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
import ReplayRoundedIcon from "@mui/icons-material/ReplayRounded";

import { TYPOGRAPHY } from "../../../theme/typography";
import {
  calendarPrimaryButtonSx,
  calendarSecondaryButtonSx,
} from "../calendarGlassSx";

const buttonSx = {
  ...calendarPrimaryButtonSx,
  minHeight: 42,
  px: { xs: 1.1, sm: 1.6 },
  minWidth: 0,
  flex: { xs: 1, sm: "0 1 auto" },
  whiteSpace: "nowrap",
  ...TYPOGRAPHY.button,
};

const secondaryButtonSx = {
  ...calendarSecondaryButtonSx,
  minHeight: 42,
  px: { xs: 1.1, sm: 1.6 },
  minWidth: 0,
  flex: { xs: 1, sm: "0 1 auto" },
  whiteSpace: "nowrap",
  ...TYPOGRAPHY.button,
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
        px: { xs: 1.5, sm: 2.5 },
        py: 1.25,
        borderTop: "1px solid",
        borderColor: "#E7EAF2",
        background: "#FFFFFF",
        flexShrink: 0,
      }}
    >
      <Stack
        direction={{ xs: "column", sm: "row" }}
        alignItems={{ xs: "stretch", sm: "center" }}
        spacing={1}
      >
        {/* Primary + secondary actions, grouped left */}

        <Stack
          direction="row"
          spacing={1}
          sx={{ flex: 1, minWidth: 0, width: "100%" }}
        >
          {status === "DRAFT" && (
            <>
              <Button
                variant="contained"
                disableElevation
                startIcon={<PublishRoundedIcon />}
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
                startIcon={<PublishRoundedIcon />}
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
              startIcon={<ReplayRoundedIcon />}
              onClick={() => handleAction(onRetry)}
              disabled={loading}
              sx={{
                ...buttonSx,
                background: "#DC2626",
                "&:hover": { background: "#B91C1C", boxShadow: "0 6px 14px rgba(185,28,28,0.2)" },
              }}
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
                borderColor: "#F1C7CE",
                background: "#FFFFFF",
                boxShadow: "none",
                color: "#C53030",
                "&:hover": {
                  bgcolor: "#FFF5F5",
                  borderColor: "#EAAAB4",
                  color: "#B42318",
                  boxShadow: "0 4px 10px rgba(176,54,79,.1)",
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
