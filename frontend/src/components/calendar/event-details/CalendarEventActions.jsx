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
  glassDialogSecondaryButtonSx,
} from "../../ui/dialog/glassDialogSx";
import { glassPrimaryButtonSx } from "../../ui/form/glassFormSx";

const buttonSx = {
  ...glassPrimaryButtonSx,
  minHeight: 42,
  px: 2,
  ...TYPOGRAPHY.button,
};

const secondaryButtonSx = {
  ...glassDialogSecondaryButtonSx,
  minHeight: 42,
  px: 2,
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
        px: { xs: 2.5, sm: 3 },
        py: 1.5,
        borderTop: "1px solid",
        borderColor: "rgba(190,211,242,0.68)",
        background: "linear-gradient(180deg, rgba(248,252,255,0.98), rgba(230,241,255,0.98))",
        boxShadow: "0 -8px 22px rgba(72,105,157,0.08), inset 0 1px 0 rgba(255,255,255,0.96)",
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
                borderColor: "rgba(194,214,246,0.86)",
                background: "linear-gradient(145deg, rgba(255,255,255,0.96), rgba(232,242,255,0.9))",
                boxShadow: "0 4px 10px rgba(70,106,172,0.08), inset 0 1px 0 #FFFFFF",
                color: "text.secondary",
                "&:hover": {
                  bgcolor: "error.lighter",
                  borderColor: "error.light",
                  color: "error.dark",
                background: "linear-gradient(145deg, rgba(255,244,246,.98), rgba(255,231,235,.94))",
                boxShadow: "0 5px 12px rgba(176,54,79,.12), inset 0 1px 0 #fff",
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
