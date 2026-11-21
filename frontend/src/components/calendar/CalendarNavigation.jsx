import {
  Box,
  Button,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";

import ChevronLeftRoundedIcon from "@mui/icons-material/ChevronLeftRounded";
import ChevronRightRoundedIcon from "@mui/icons-material/ChevronRightRounded";
import KeyboardArrowDownRoundedIcon from "@mui/icons-material/KeyboardArrowDownRounded";

import { useState } from "react";
import dayjs from "dayjs";

import { TYPOGRAPHY } from "../../theme/typography";
import { calendarGlassControlSx, calendarGlassSurfaceSx } from "./calendarGlassSx";

export default function CalendarNavigation({
  currentDate,
  onPrevious,
  onNext,
  onToday,
  onDateChange,
}) {
  const [monthPickerOpen, setMonthPickerOpen] =
    useState(false);

  const currentMonth = currentDate.month();

  const currentYear = currentDate.year();

  const months = Array.from(
    { length: 12 },
    (_, index) =>
      dayjs()
        .year(currentYear)
        .month(index)
        .format("MMM"),
  );

  function handleMonthSelect(monthIndex) {
    const nextDate = currentDate
      .year(currentYear)
      .month(monthIndex);

    onDateChange?.(nextDate);

    setMonthPickerOpen(false);
  }

  return (
    <Stack
      direction="row"
      alignItems="center"
      spacing={{
        xs: 0.5,
        sm: 1,
      }}
      sx={{
        flexShrink: 0,

        // Keeps the dropdown positioned
        // relative to the navigation area.
        position: "relative",

        // Keeps navigation above nearby content.
        zIndex: 20,

        // Prevents internal clipping.
        overflow: "visible",
      }}
    >
      {/* ========================================
          PREVIOUS MONTH
      ======================================== */}

      <IconButton
        onClick={onPrevious}
        aria-label="Previous month"
        sx={{
          width: { xs: 36, sm: 42 },
          height: { xs: 36, sm: 42 },

          ...calendarGlassControlSx,
          borderRadius: "50%",

          color: "text.primary",

          flexShrink: 0,

          "&:hover": {
            bgcolor: "#F5F2FF",
            borderColor: "#C9BDF7",
            color: "#6D45D9",
          },
        }}
      >
        <ChevronLeftRoundedIcon />
      </IconButton>

      {/* ========================================
          TODAY
      ======================================== */}

      <Button
        onClick={onToday}
        sx={{
          height: 42,

          minWidth: {
            xs: 60,
            sm: 78,
          },

          px: {
            xs: 1.25,
            sm: 2,
          },

          borderRadius: "12px",

          color: "text.primary",

          ...calendarGlassControlSx,

          flexShrink: 0,

          ...TYPOGRAPHY.button,

          "&:hover": {
            bgcolor: "#F8FAFF",
            borderColor: "#B8C7E7",
          },
        }}
      >
        Today
      </Button>

      {/* ========================================
          NEXT MONTH
      ======================================== */}

      <IconButton
        onClick={onNext}
        aria-label="Next month"
        sx={{
          width: { xs: 36, sm: 42 },
          height: { xs: 36, sm: 42 },

          ...calendarGlassControlSx,
          borderRadius: "50%",

          color: "text.primary",

          flexShrink: 0,

          "&:hover": {
            bgcolor: "#F5F2FF",
            borderColor: "#C9BDF7",
            color: "#6D45D9",
          },
        }}
      >
        <ChevronRightRoundedIcon />
      </IconButton>

      {/* ========================================
          MONTH SELECTOR
      ======================================== */}

      <Box
        sx={{
          position: "relative",

          ml: {
            xs: 0.5,
            sm: 1,
          },

          flexShrink: 0,

          // Important for dropdown visibility.
          overflow: "visible",
        }}
      >
        <Button
          onClick={() =>
            setMonthPickerOpen(
              (current) => !current,
            )
          }
          endIcon={
            <KeyboardArrowDownRoundedIcon
              sx={{
                fontSize: 20,
              }}
            />
          }
          sx={{
            height: 42,

            minWidth: {
            xs: 118,
              sm: 148,
            },

            px: {
            xs: 1.25,
              sm: 2,
            },

            justifyContent: "space-between",

            border: "1px solid",

            borderRadius: "12px",

            ...calendarGlassControlSx,
            borderColor: monthPickerOpen ? "#9B83EB" : undefined,
            bgcolor: monthPickerOpen ? "#F5F2FF" : undefined,

            color: "text.primary",

            flexShrink: 0,

            ...TYPOGRAPHY.button,

            "&:hover": {
              bgcolor: "#F5F2FF",
              borderColor: "#C9BDF7",
            },
          }}
        >
          {currentDate.format("MMMM YYYY")}
        </Button>

        {/* ======================================
            MONTH DROPDOWN
        ====================================== */}

        {monthPickerOpen && (
          <Box
            sx={{
              position: "absolute",

              top: "calc(100% + 8px)",

              left: 0,

              // Higher than toolbar and calendar content.
              zIndex: 1300,

              width: {
                xs: 280,
                sm: 320,
              },

              p: 2,

              ...calendarGlassSurfaceSx,
              borderRadius: "16px",
              boxShadow: "0 16px 34px rgba(54,76,132,0.14)",

              boxSizing: "border-box",
            }}
          >
            {/* ==================================
                YEAR
            ================================== */}

            <Stack
              direction="row"
              alignItems="center"
              justifyContent="space-between"
              sx={{
                mb: 1.5,
              }}
            >
              <Typography
                sx={{ ...TYPOGRAPHY.cardTitle, color: "#142D59", fontWeight: 700 }}
              >
                {currentYear}
              </Typography>
            </Stack>

            {/* ==================================
                MONTHS
            ================================== */}

            <Box
              sx={{
                display: "grid",

                gridTemplateColumns:
                  "repeat(3, 1fr)",

                gap: 0.75,
              }}
            >
              {months.map(
                (month, index) => {
                  const selected =
                    index === currentMonth;

                  return (
                    <Button
                      key={month}
                      onClick={() =>
                        handleMonthSelect(
                          index,
                        )
                      }
                      sx={{
                        minHeight: 40,

                        borderRadius: 2,

                        color: selected ? "#6741D9" : "text.primary",

                        bgcolor: selected ? "#F1EBFF" : "#FFFFFF",
                        border: "1px solid",
                        borderColor: selected ? "#D8CCFF" : "#E7EAF3",
                        boxShadow: selected ? "0 2px 6px rgba(92,65,190,0.08)" : "none",

                        ...TYPOGRAPHY.button,

                        "&:hover": {
                          bgcolor: "#F8F7FF",
                        },
                      }}
                    >
                      {month}
                    </Button>
                  );
                },
              )}
            </Box>
          </Box>
        )}
      </Box>
    </Stack>
  );
}
