import {
  Box,
  Button,
  Paper,
} from "@mui/material";

import FilterListRoundedIcon from "@mui/icons-material/FilterListRounded";

import CalendarNavigation from "./CalendarNavigation";
import CalendarSearch from "./CalendarSearch";

import { TYPOGRAPHY } from "../../theme/typography";

export default function CalendarToolbar({
  currentDate,
  search,
  onPrevious,
  onNext,
  onToday,
  onDateChange,
  onSearchChange,
  onFiltersChange,
  activeFilterCount = 0,
}) {
  return (
    <Paper
      elevation={0}
      sx={{
        width: "100%",

        border: "1px solid",
        borderColor: "divider",

        borderRadius: 3,

        bgcolor: "background.paper",

        px: {
          xs: 1.5,
          sm: 2,
          md: 2.5,
        },

        py: 1.5,

        boxSizing: "border-box",

        // Important:
        // Allows the month dropdown to extend
        // outside the toolbar without being clipped.
        overflow: "visible",

        position: "relative",

        zIndex: 10,
      }}
    >
      <Box
        sx={{
          width: "100%",

          display: "grid",

          gridTemplateColumns: {
            xs: "1fr",
            md: "auto 1fr",
          },

          alignItems: "center",

          columnGap: {
            xs: 2,
            md: 3,
          },

          rowGap: 1.5,

          // Allow absolutely positioned
          // navigation dropdowns to remain visible.
          overflow: "visible",
        }}
      >
        {/* ======================================
            LEFT
            CALENDAR NAVIGATION
        ====================================== */}

        <Box
          sx={{
            minWidth: 0,

            display: "flex",

            alignItems: "center",

            justifyContent: "flex-start",

            // IMPORTANT:
            // Do not use overflowX: auto here.
            // It clips the month dropdown.
            overflow: "visible",

            position: "relative",

            zIndex: 20,
          }}
        >
          <CalendarNavigation
            currentDate={currentDate}
            onPrevious={onPrevious}
            onNext={onNext}
            onToday={onToday}
            onDateChange={onDateChange}
          />
        </Box>

        {/* ======================================
            RIGHT
            SEARCH + FILTER
        ====================================== */}

        <Box
          sx={{
            minWidth: 0,

            display: "flex",

            alignItems: "center",

            justifyContent: {
              xs: "flex-start",
              md: "flex-end",
            },

            gap: 1.25,
          }}
        >
          <CalendarSearch
            value={search}
            onChange={onSearchChange}
          />

          {/* ==================================
              FILTER BUTTON
          ================================== */}

          <Button
            variant="outlined"
            startIcon={
              <FilterListRoundedIcon />
            }
            onClick={onFiltersChange}
            sx={{
              height: 44,

              minWidth: 112,

              px: 2,

              flexShrink: 0,

              borderRadius: 2,

              borderColor: "divider",

              bgcolor: "background.paper",

              color: "text.primary",

              ...TYPOGRAPHY.button,

              "&:hover": {
                bgcolor: "action.hover",

                borderColor:
                  "text.disabled",
              },
            }}
          >
            Filters

            {activeFilterCount > 0 && (
              <Box
                component="span"
                sx={{
                  ml: 1,

                  minWidth: 20,

                  height: 20,

                  px: 0.5,

                  display: "inline-flex",

                  alignItems: "center",

                  justifyContent: "center",

                  borderRadius: "50%",

                  bgcolor:
                    "primary.main",

                  color:
                    "primary.contrastText",

                  ...TYPOGRAPHY.caption,

                  fontWeight: 700,
                }}
              >
                {activeFilterCount}
              </Box>
            )}
          </Button>
        </Box>
      </Box>
    </Paper>
  );
}