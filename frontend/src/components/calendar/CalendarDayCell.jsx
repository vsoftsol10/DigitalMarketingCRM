import { Box, Typography } from "@mui/material";
import dayjs from "dayjs";

import { TYPOGRAPHY } from "../../theme/typography";
import CalendarEvent from "./CalendarEvent";
import { calendarGlassInsetSx } from "./calendarGlassSx";

function eventTimeMinutes(time) {
  const match = String(time || "").match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
  if (!match) {
    return Number.MAX_SAFE_INTEGER;
  }

  let hours = Number(match[1]);
  const minutes = Number(match[2]);
  const period = match[3].toUpperCase();

  if (period === "PM" && hours !== 12) {
    hours += 12;
  } else if (period === "AM" && hours === 12) {
    hours = 0;
  }

  return hours * 60 + minutes;
}

export default function CalendarDayCell({
  date,
  currentDate,
  events = [],
  onEventClick,
}) {
  const isCurrentMonth =
    date.month() === currentDate.month() && date.year() === currentDate.year();

  const isToday = date.isSame(dayjs(), "day");

  const dayEvents = events
    .filter(
      (event) => event.date && dayjs(event.date).isSame(date, "day"),
    )
    .sort((left, right) => eventTimeMinutes(left.time) - eventTimeMinutes(right.time));

  return (
    <Box
      sx={{
        minHeight: {
          xs: 96,
          sm: 118,
          md: 136,
        },

        p: { xs: 0.5, sm: 0.75, md: 1 },

        borderRight: "1px solid",
        borderBottom: "1px solid",
        borderColor: "#E7EAF2",

        background: isCurrentMonth
          ? "#FFFFFF"
          : "#F8FAFF",
        ...(isCurrentMonth ? {} : calendarGlassInsetSx),
        transition: "background-color 160ms ease",
        "&:hover": { background: "#FCFBFF" },

        "&:nth-of-type(7n)": {
          borderRight: "none",
        },
      }}
    >
      {/* Day Number */}

      <Box
        sx={{
          display: "flex",
          justifyContent: "flex-start",
          mb: { xs: 0.5, sm: 0.75 },
        }}
      >
        <Box
          sx={{
            width: { xs: 26, sm: 28 },
            height: { xs: 26, sm: 28 },

            display: "flex",
            alignItems: "center",
            justifyContent: "center",

            borderRadius: "50%",

            bgcolor: isToday ? "#7046E8" : "transparent",
            boxShadow: isToday ? "0 3px 8px rgba(112,70,232,0.22)" : "none",

            color: isToday
              ? "primary.contrastText"
              : isCurrentMonth
                ? "text.primary"
                : "text.disabled",
          }}
        >
          <Typography
            sx={{
              ...TYPOGRAPHY.bodySmall,

              fontWeight: isToday ? 700 : 500,

              color: "inherit",
            }}
          >
            {date.date()}
          </Typography>
        </Box>
      </Box>

      {/* Events */}

      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: 0.75,
        }}
      >
        {dayEvents.map((event) => (
          <CalendarEvent key={event.id} event={event} onClick={onEventClick} />
        ))}
      </Box>
    </Box>
  );
}
