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
import {
  calendarPrimaryButtonSx,
  calendarSecondaryButtonSx,
} from "../calendarGlassSx";

const scheduleFieldSx = {
  "& .MuiOutlinedInput-root": {
    minHeight: 46,
    borderRadius: "12px",
    background: "#FFFFFF",
    "& fieldset": { borderColor: "#D7DFF0" },
    "&:hover fieldset": { borderColor: "#B8C7E7" },
    "&.Mui-focused fieldset": { borderColor: "#8A72E6" },
    "&.Mui-focused": { boxShadow: "0 0 0 3px rgba(111,93,236,0.11)" },
  },
};

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
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          width: "calc(100% - 32px)",
          maxWidth: 480,
          maxHeight: "calc(100dvh - 32px)",
          m: { xs: 2, sm: 3 },
          border: "1px solid #DCE3F1",
          borderRadius: "18px",
          background: "#FFFFFF",
          boxShadow: "0 14px 36px rgba(36,52,94,0.14)",
        },
      }}
    >
      <DialogTitle
        sx={{
          ...TYPOGRAPHY.sectionTitle,
          color: "#142D59",
          px: { xs: 2.25, sm: 3 },
          py: 2.25,
          background: "#FFFFFF",
        }}
      >
        {isReschedule ? "Reschedule post" : "Schedule post"}
      </DialogTitle>

      <Divider sx={{ borderColor: "#E7EAF2" }} />

      <DialogContent
        sx={{
          px: { xs: 2.25, sm: 3 },
          py: 2.5,
          overflowY: "auto",
          background: "#FFFFFF",
        }}
      >
        <Stack component="form" id="calendar-schedule-form" spacing={2} onSubmit={handleSubmit}>
          <TextField
            label="Publish date"
            type="date"
            value={values.publish_date}
            onChange={handleChange("publish_date")}
            InputLabelProps={{ shrink: true }}
            required
            fullWidth
            sx={scheduleFieldSx}
          />
          <TextField
            label="Publish time"
            type="time"
            value={values.publish_time}
            onChange={handleChange("publish_time")}
            InputLabelProps={{ shrink: true }}
            required
            fullWidth
            sx={scheduleFieldSx}
          />
          <TextField
            label="Timezone"
            value={values.timezone}
            onChange={handleChange("timezone")}
            required
            fullWidth
            sx={scheduleFieldSx}
          />
        </Stack>
      </DialogContent>

      <Divider sx={{ borderColor: "#E7EAF2" }} />

      <DialogActions
        sx={{
          px: { xs: 2.25, sm: 3 },
          py: 2,
          gap: 1,
          flexWrap: "wrap",
          justifyContent: "flex-end",
          background: "#FFFFFF",
        }}
      >
        <Button disabled={loading} variant="outlined" onClick={onClose} sx={{ ...calendarSecondaryButtonSx, minHeight: 42, borderRadius: "11px", flex: { xs: "1 1 120px", sm: "0 0 auto" } }}>
          Cancel
        </Button>
        <Button
          disabled={loading}
          variant="contained"
          form="calendar-schedule-form"
          type="submit"
          sx={{ ...calendarPrimaryButtonSx, minHeight: 42, borderRadius: "11px", flex: { xs: "1 1 150px", sm: "0 0 auto" } }}
        >
          {loading
            ? loadingAction === "reschedule" ? "Rescheduling..." : "Scheduling..."
            : isReschedule ? "Reschedule" : "Schedule"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
