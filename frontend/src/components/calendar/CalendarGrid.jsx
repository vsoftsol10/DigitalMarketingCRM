import { Box, Typography } from "@mui/material";
import dayjs from "dayjs";

import CalendarDayCell from "./CalendarDayCell";

import { TYPOGRAPHY } from "../../theme/typography";

const WEEK_DAYS = [
  "Sun",
  "Mon",
  "Tue",
  "Wed",
  "Thu",
  "Fri",
  "Sat",
];

function createCalendarDays(currentDate) {
  const startOfMonth =
    currentDate.startOf("month");

  const endOfMonth =
    currentDate.endOf("month");

  const firstDay =
    startOfMonth.day();

  const daysInMonth =
    endOfMonth.date();

  const previousMonthDays = [];

  for (
    let i = firstDay - 1;
    i >= 0;
    i--
  ) {
    previousMonthDays.push(
      startOfMonth.subtract(
        i + 1,
        "day",
      ),
    );
  }

  const currentMonthDays = [];

  for (
    let day = 1;
    day <= daysInMonth;
    day++
  ) {
    currentMonthDays.push(
      startOfMonth.date(day),
    );
  }

  const totalDays =
    previousMonthDays.length +
    currentMonthDays.length;

  const remainingDays =
    totalDays % 7 === 0
      ? 0
      : 7 - (totalDays % 7);

  const nextMonthDays = [];

  for (
    let i = 1;
    i <= remainingDays;
    i++
  ) {
    nextMonthDays.push(
      endOfMonth.add(i, "day"),
    );
  }

  return [
    ...previousMonthDays,
    ...currentMonthDays,
    ...nextMonthDays,
  ];
}

export default function CalendarGrid({
  currentDate = dayjs(),
  events = [],
  filters = {},
  onEventClick,
}) {
  const calendarDays =
    createCalendarDays(currentDate);

  return (
    <Box
      sx={{
        width: "100%",

        border: "1px solid",
        borderColor: "divider",

        borderRadius: 3,

        bgcolor: "background.paper",

        overflow: "hidden",
      }}
    >
      {/* =================================
          WEEK HEADER
      ================================= */}

      <Box
        sx={{
          display: "grid",

          gridTemplateColumns:
            "repeat(7, minmax(0, 1fr))",

          borderBottom: "1px solid",

          borderColor: "divider",

          bgcolor: "background.paper",
        }}
      >
        {WEEK_DAYS.map((day) => (
          <Box
            key={day}
            sx={{
              minHeight: 44,

              px: 1.5,

              display: "flex",

              alignItems: "center",

              justifyContent: "center",

              borderRight: "1px solid",

              borderColor: "divider",

              "&:last-child": {
                borderRight: "none",
              },
            }}
          >
            <Typography
              sx={{
                ...TYPOGRAPHY.inputLabel,

                fontWeight: 600,

                color: "text.secondary",
              }}
            >
              {day}
            </Typography>
          </Box>
        ))}
      </Box>

      {/* =================================
          CALENDAR DAYS
      ================================= */}

      <Box
        sx={{
          display: "grid",

          gridTemplateColumns:
            "repeat(7, minmax(0, 1fr))",
        }}
      >
        {calendarDays.map((date) => (
          <CalendarDayCell
            key={date.format(
              "YYYY-MM-DD",
            )}
            date={date}
            currentDate={currentDate}
            events={events}
            onEventClick={
              onEventClick
            }
          />
        ))}
      </Box>
    </Box>
  );
}