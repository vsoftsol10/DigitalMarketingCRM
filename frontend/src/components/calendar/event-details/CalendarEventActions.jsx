import {
  Box,
  Button,
  IconButton,
  Stack,
  Tooltip,
} from "@mui/material";

import EditRoundedIcon from "@mui/icons-material/EditRounded";
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
  onEdit,
  onReschedule,
  onPublishNow,
  onRetry,
  onDelete,
}) {
  if (!event) {
    return null;
  }

  const status = event.status?.toUpperCase();
  const handleAction = (callback) => callback?.(event);
  const canDelete = status !== "PUBLISHED";

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
                startIcon={<EditRoundedIcon />}
                onClick={() => handleAction(onEdit)}
                sx={buttonSx}
              >
                Edit post
              </Button>

              <Button
                variant="outlined"
                startIcon={<ScheduleRoundedIcon />}
                onClick={() =>
                  handleAction(onReschedule)
                }
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
                sx={secondaryButtonSx}
              >
                Publish now
              </Button>
            </>
          )}

          {status === "PUBLISHED" && (
            <Button
              variant="outlined"
              startIcon={<EditRoundedIcon />}
              onClick={() => handleAction(onEdit)}
              sx={secondaryButtonSx}
            >
              View post
            </Button>
          )}

          {status === "FAILED" && (
            <>
              <Button
                variant="contained"
                disableElevation
                color="error"
                startIcon={<ReplayRoundedIcon />}
                onClick={() => handleAction(onRetry)}
                sx={buttonSx}
              >
                Retry publishing
              </Button>

              <Button
                variant="outlined"
                startIcon={<EditRoundedIcon />}
                onClick={() => handleAction(onEdit)}
                sx={secondaryButtonSx}
              >
                Edit post
              </Button>
            </>
          )}
        </Stack>

        {/* Quiet, icon-only delete — kept out of the primary
            action group so it can't be mis-tapped */}

        {canDelete && (
          <Tooltip title="Delete post">
            <IconButton
              aria-label="Delete post"
              onClick={() => handleAction(onDelete)}
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