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
        xs: 0.75,
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
          width: 44,
          height: 44,

          ...calendarGlassControlSx,
          borderRadius: "50%",

          color: "text.primary",

          flexShrink: 0,

          "&:hover": {
            bgcolor: "#E4F0FF",
            borderColor: "#B5CEF4",
            boxShadow: "0 7px 14px rgba(70,106,172,0.18)",
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
          height: 44,

          minWidth: {
            xs: 70,
            sm: 78,
          },

          px: {
            xs: 1.5,
            sm: 2,
          },

          borderRadius: 999,

          color: "text.primary",

          ...calendarGlassControlSx,

          flexShrink: 0,

          ...TYPOGRAPHY.button,

          "&:hover": {
            bgcolor: "#E4F0FF",
            boxShadow: "0 7px 14px rgba(70,106,172,0.16)",
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
          width: 44,
          height: 44,

          ...calendarGlassControlSx,
          borderRadius: "50%",

          color: "text.primary",

          flexShrink: 0,

          "&:hover": {
            bgcolor: "#E4F0FF",
            borderColor: "#B5CEF4",
            boxShadow: "0 7px 14px rgba(70,106,172,0.18)",
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
            height: 44,

            minWidth: {
              xs: 130,
              sm: 148,
            },

            px: {
              xs: 1.75,
              sm: 2,
            },

            justifyContent: "space-between",

            border: "1px solid",

            borderRadius: 999,

            ...calendarGlassControlSx,
            borderColor: monthPickerOpen ? "#7CAAF4" : "rgba(255,255,255,0.96)",
            bgcolor: monthPickerOpen ? "#E5F0FF" : undefined,

            color: "text.primary",

            flexShrink: 0,

            ...TYPOGRAPHY.button,

            "&:hover": {
              bgcolor: "#E4F0FF",
              borderColor: "#B5CEF4",
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
              borderRadius: 3.5,
              boxShadow: "0 18px 38px rgba(58,94,155,0.2), inset 0 1px 0 #FFFFFF",

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
                sx={{ ...TYPOGRAPHY.cardTitle, color: "#203765", fontWeight: 750 }}
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

                        color: selected ? "#1458C6" : "text.primary",

                        bgcolor: selected ? "#DDEBFF" : "rgba(255,255,255,0.28)",
                        border: "1px solid",
                        borderColor: selected ? "#AFC9F3" : "transparent",
                        boxShadow: selected ? "0 4px 10px rgba(64,107,178,0.14), inset 0 1px 0 #FFFFFF" : "none",

                        ...TYPOGRAPHY.button,

                        "&:hover": {
                          bgcolor:
                            "rgba(221,235,255,0.82)",
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
