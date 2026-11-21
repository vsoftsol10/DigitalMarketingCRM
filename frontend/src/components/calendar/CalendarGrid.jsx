import { Box, Typography } from "@mui/material";
import dayjs from "dayjs";

import CalendarDayCell from "./CalendarDayCell";

import { TYPOGRAPHY } from "../../theme/typography";
import { calendarGlassSurfaceSx } from "./calendarGlassSx";

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
  onEventClick,
}) {
  const calendarDays =
    createCalendarDays(currentDate);

  return (
    <Box
      sx={{
        width: "100%",

        ...calendarGlassSurfaceSx,
        borderRadius: { xs: "16px", sm: "18px" },

        overflow: "hidden",
        overflowX: { xs: "auto", sm: "hidden" },
        overflowY: "hidden",
        "&::-webkit-scrollbar": { height: 6 },
        "&::-webkit-scrollbar-thumb": { background: "#CCD5E5", borderRadius: 8 },
      }}
    >
      <Box sx={{ minWidth: { xs: 680, md: 720, lg: 0 } }}>
      {/* =================================
          WEEK HEADER
      ================================= */}

      <Box
        sx={{
          display: "grid",

          gridTemplateColumns:
            "repeat(7, minmax(0, 1fr))",

          borderBottom: "1px solid",

          borderColor: "#E3E8F2",
          background: "#F8FAFF",
        }}
      >
        {WEEK_DAYS.map((day) => (
          <Box
            key={day}
            sx={{
              minHeight: { xs: 38, sm: 42 },

              px: { xs: 0.5, sm: 1 },

              display: "flex",

              alignItems: "center",

              justifyContent: "center",

              borderRight: "1px solid",

              borderColor: "#E7EAF2",

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
    </Box>
  );
}
