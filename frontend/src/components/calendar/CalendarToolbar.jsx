import {
  Box,
  Button,
  Paper,
} from "@mui/material";

import FilterListRoundedIcon from "@mui/icons-material/FilterListRounded";

import CalendarNavigation from "./CalendarNavigation";
import CalendarSearch from "./CalendarSearch";

import { TYPOGRAPHY } from "../../theme/typography";
import { calendarGlassSurfaceSx } from "./calendarGlassSx";

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

        ...calendarGlassSurfaceSx,

        borderRadius: { xs: "16px", sm: "18px" },

        px: {
          xs: 1.5,
          sm: 2,
          md: 2.5,
        },

        py: { xs: 1.25, sm: 1.5 },

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

            gap: 1,
            flexWrap: { xs: "wrap", md: "nowrap" },
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
              height: 42,

              minWidth: { xs: 100, sm: 112 },

              px: 2,

              flexShrink: 0,

              borderRadius: "12px",
              borderColor: "#D7DFF0",
              background: "#FFFFFF",
              boxShadow: "0 2px 6px rgba(54,76,132,0.04)",
              color: "#405778",

              ...TYPOGRAPHY.button,

              "&:hover": {
                bgcolor: "#F8FAFF",
                borderColor: "#B8C7E7",
                boxShadow: "0 4px 10px rgba(54,76,132,0.08)",
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
