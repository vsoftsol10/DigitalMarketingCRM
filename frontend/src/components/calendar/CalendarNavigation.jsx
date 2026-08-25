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

          border: "1px solid",
          borderColor: "divider",

          bgcolor: "background.paper",

          color: "text.primary",

          flexShrink: 0,

          "&:hover": {
            bgcolor: "action.hover",
            borderColor: "text.disabled",
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

          borderRadius: 2,

          color: "text.primary",

          bgcolor: "background.paper",

          flexShrink: 0,

          ...TYPOGRAPHY.button,

          "&:hover": {
            bgcolor: "action.hover",
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

          border: "1px solid",
          borderColor: "divider",

          bgcolor: "background.paper",

          color: "text.primary",

          flexShrink: 0,

          "&:hover": {
            bgcolor: "action.hover",
            borderColor: "text.disabled",
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

            borderColor: monthPickerOpen
              ? "primary.main"
              : "divider",

            borderRadius: 2,

            bgcolor: monthPickerOpen
              ? "action.selected"
              : "background.paper",

            color: "text.primary",

            flexShrink: 0,

            ...TYPOGRAPHY.button,

            "&:hover": {
              bgcolor: "action.hover",

              borderColor:
                "text.disabled",
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

              bgcolor: "background.paper",

              border: "1px solid",
              borderColor: "divider",

              borderRadius: 2.5,

              boxShadow:
                "0 12px 32px rgba(15, 23, 42, 0.12)",

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
                sx={TYPOGRAPHY.cardTitle}
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

                        borderRadius: 1.5,

                        color: selected
                          ? "primary.main"
                          : "text.primary",

                        bgcolor: selected
                          ? "action.selected"
                          : "transparent",

                        ...TYPOGRAPHY.button,

                        "&:hover": {
                          bgcolor:
                            "action.hover",
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