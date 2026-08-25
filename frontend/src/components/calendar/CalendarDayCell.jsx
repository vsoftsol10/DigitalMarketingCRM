import { Box, Typography } from "@mui/material";
import dayjs from "dayjs";

import { TYPOGRAPHY } from "../../theme/typography";
import CalendarEvent from "./CalendarEvent";

export default function CalendarDayCell({
  date,
  currentDate,
  events = [],
  onEventClick,
}) {
  const isCurrentMonth =
    date.month() === currentDate.month() && date.year() === currentDate.year();

  const isToday = date.isSame(dayjs(), "day");

  const dayEvents = events.filter(
    (event) => event.date && dayjs(event.date).isSame(date, "day"),
  );

  return (
    <Box
      sx={{
        minHeight: {
          xs: 110,
          sm: 135,
          md: 150,
        },

        p: 1,

        borderRight: "1px solid",
        borderBottom: "1px solid",
        borderColor: "divider",

        bgcolor: isCurrentMonth ? "background.paper" : "action.hover",

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
          mb: 1,
        }}
      >
        <Box
          sx={{
            width: 30,
            height: 30,

            display: "flex",
            alignItems: "center",
            justifyContent: "center",

            borderRadius: "50%",

            bgcolor: isToday ? "primary.main" : "transparent",

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
