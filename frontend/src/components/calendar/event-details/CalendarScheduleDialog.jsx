import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Stack,
  TextField,
} from "@mui/material";

import { useEffect, useState } from "react";

import dayjs from "dayjs";

import { TYPOGRAPHY } from "../../../theme/typography";
import { glassPrimaryButtonSx } from "../../ui/form/glassFormSx";
import {
  glassDialogActionsSx,
  glassDialogContentSx,
  glassDialogPaperSx,
  glassDialogSecondaryButtonSx,
  glassDialogTitleSx,
} from "../../ui/dialog/glassDialogSx";

function toTimeValue(value) {
  const match = String(value || "").match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
  if (!match) {
    return "";
  }

  let hours = Number(match[1]);
  const minutes = match[2];
  const period = match[3].toUpperCase();

  if (period === "PM" && hours !== 12) {
    hours += 12;
  }
  if (period === "AM" && hours === 12) {
    hours = 0;
  }

  return `${String(hours).padStart(2, "0")}:${minutes}`;
}

function getInitialValues(event) {
  const defaultDateTime = dayjs().add(1, "hour").startOf("hour");
  const eventDate = dayjs(event?.date);

  return {
    publish_date: eventDate.isValid()
      ? eventDate.format("YYYY-MM-DD")
      : defaultDateTime.format("YYYY-MM-DD"),
    publish_time: toTimeValue(event?.time) || defaultDateTime.format("HH:mm"),
    timezone: event?.timezone || "UTC",
  };
}

export default function CalendarScheduleDialog({
  open,
  event,
  loading = false,
  loadingAction = null,
  onClose,
  onConfirm,
}) {
  const [values, setValues] = useState(() => getInitialValues(event));

  useEffect(() => {
    if (open) {
      setValues(getInitialValues(event));
    }
  }, [event, open]);

  const isReschedule = event?.status?.toUpperCase() === "SCHEDULED";

  function handleChange(field) {
    return (changeEvent) => {
      setValues((current) => ({
        ...current,
        [field]: changeEvent.target.value,
      }));
    };
  }

  function handleSubmit(changeEvent) {
    changeEvent.preventDefault();
    onConfirm?.(values);
  }

  return (
    <Dialog
      open={open}
      onClose={loading ? undefined : onClose}
      maxWidth="xs"
      fullWidth
      PaperProps={{ sx: glassDialogPaperSx }}
    >
      <DialogTitle
        sx={{ ...TYPOGRAPHY.sectionTitle, ...glassDialogTitleSx }}
      >
        {isReschedule ? "Reschedule post" : "Schedule post"}
      </DialogTitle>

      <Divider sx={{ borderColor: "rgba(146,168,201,.22)" }} />

      <DialogContent sx={glassDialogContentSx}>
        <Stack component="form" id="calendar-schedule-form" spacing={2} onSubmit={handleSubmit}>
          <TextField
            label="Publish date"
            type="date"
            value={values.publish_date}
            onChange={handleChange("publish_date")}
            InputLabelProps={{ shrink: true }}
            required
            fullWidth
          />
          <TextField
            label="Publish time"
            type="time"
            value={values.publish_time}
            onChange={handleChange("publish_time")}
            InputLabelProps={{ shrink: true }}
            required
            fullWidth
          />
          <TextField
            label="Timezone"
            value={values.timezone}
            onChange={handleChange("timezone")}
            required
            fullWidth
          />
        </Stack>
      </DialogContent>

      <Divider sx={{ borderColor: "rgba(146,168,201,.22)" }} />

      <DialogActions sx={glassDialogActionsSx}>
        <Button disabled={loading} variant="outlined" onClick={onClose} sx={glassDialogSecondaryButtonSx}>
          Cancel
        </Button>
        <Button
          disabled={loading}
          variant="contained"
          form="calendar-schedule-form"
          type="submit"
          sx={glassPrimaryButtonSx}
        >
          {loading
            ? loadingAction === "reschedule" ? "Rescheduling..." : "Scheduling..."
            : isReschedule ? "Reschedule" : "Schedule"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
