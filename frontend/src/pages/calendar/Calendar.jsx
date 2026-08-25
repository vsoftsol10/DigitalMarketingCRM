// import { Box } from "@mui/material";

// import { useMemo, useState } from "react";

// import dayjs from "dayjs";

// import CalendarHeader from "../../components/calendar/CalendarHeader";
// import CalendarToolbar from "../../components/calendar/CalendarToolbar";
// import CalendarGrid from "../../components/calendar/CalendarGrid";
// import CalendarFilters from "../../components/calendar/CalendarFilters";
// import CalendarEventDetails from "../../components/calendar/CalendarEventDetails";

// const DEFAULT_FILTERS = {
//   organization: "",
//   platform: "",
//   contentType: "",
//   status: "",
// };

// export default function Calendar() {
//   // ==========================================
//   // CURRENT CALENDAR DATE
//   // ==========================================

//   const [currentDate, setCurrentDate] = useState(dayjs());

//   // ==========================================
//   // SEARCH
//   // ==========================================

//   const [search, setSearch] = useState("");

//   // ==========================================
//   // FILTERS
//   // ==========================================

//   const [filters, setFilters] = useState(DEFAULT_FILTERS);

//   const [appliedFilters, setAppliedFilters] = useState(DEFAULT_FILTERS);

//   // ==========================================
//   // FILTER DRAWER
//   // ==========================================

//   const [filtersOpen, setFiltersOpen] = useState(false);
//   const [selectedEvent, setSelectedEvent] = useState(null);
//   const [eventDetailsOpen, setEventDetailsOpen] = useState(false);

//   // ==========================================
//   // MONTH NAVIGATION
//   // ==========================================

//   function handlePrevious() {
//     setCurrentDate((current) => current.subtract(1, "month"));
//   }

//   function handleNext() {
//     setCurrentDate((current) => current.add(1, "month"));
//   }

//   function handleToday() {
//     setCurrentDate(dayjs());
//   }

//   function handleDateChange(date) {
//     if (!date) {
//       return;
//     }

//     setCurrentDate(date);
//   }

//   function handleEventClick(event) {
//     setSelectedEvent(event);
//     setEventDetailsOpen(true);
//   }

//   function handleEventDetailsClose() {
//     setEventDetailsOpen(false);
//     setSelectedEvent(null);
//   }

//   // ==========================================
//   // SEARCH
//   // ==========================================

//   function handleSearchChange(value) {
//     setSearch(value);
//   }

//   // ==========================================
//   // FILTER CHANGE
//   // ==========================================

//   function handleFilterChange(field, value) {
//     setFilters((current) => ({
//       ...current,
//       [field]: value,
//     }));
//   }

//   // ==========================================
//   // APPLY FILTERS
//   // ==========================================

//   function handleApplyFilters() {
//     setAppliedFilters({
//       ...filters,
//     });

//     setFiltersOpen(false);
//   }

//   // ==========================================
//   // CLEAR FILTERS
//   // ==========================================

//   function handleClearFilters() {
//     const emptyFilters = {
//       ...DEFAULT_FILTERS,
//     };

//     setFilters(emptyFilters);

//     setAppliedFilters(emptyFilters);
//   }

//   // ==========================================
//   // ACTIVE FILTER COUNT
//   // ==========================================

//   const activeFilterCount = useMemo(() => {
//     return Object.values(appliedFilters).filter(Boolean).length;
//   }, [appliedFilters]);

//   // ==========================================
//   // FILTER OPTIONS
//   // ==========================================

//   /*
//     TEMPORARY UI CONFIG ONLY.

//     Later:
//     GET /api/calendar/filters/

//     இந்த data backend-லிருந்து வரும்.
//   */

//   const filterOptions = {
//     organizations: [
//       {
//         value: "ORG001",
//         label: "Lumen Coffee Co.",
//       },
//       {
//         value: "ORG002",
//         label: "Atlas Fitness",
//       },
//       {
//         value: "ORG003",
//         label: "NorthPeak Outdoors",
//       },
//     ],

//     platforms: [
//       {
//         value: "INSTAGRAM",
//         label: "Instagram",
//       },
//       {
//         value: "FACEBOOK",
//         label: "Facebook",
//       },
//       {
//         value: "LINKEDIN",
//         label: "LinkedIn",
//       },
//       {
//         value: "YOUTUBE",
//         label: "YouTube",
//       },
//       {
//         value: "THREADS",
//         label: "Threads",
//       },
//       {
//         value: "X",
//         label: "X",
//       },
//     ],

//     contentTypes: [
//       {
//         value: "POST",
//         label: "Post",
//       },
//       {
//         value: "REEL",
//         label: "Reel",
//       },
//       {
//         value: "STORY",
//         label: "Story",
//       },
//       {
//         value: "CAROUSEL",
//         label: "Carousel",
//       },
//       {
//         value: "VIDEO",
//         label: "Video",
//       },
//       {
//         value: "SHORT",
//         label: "Short",
//       },
//     ],

//     statuses: [
//       {
//         value: "SCHEDULED",
//         label: "Scheduled",
//       },
//       {
//         value: "PUBLISHED",
//         label: "Published",
//       },
//       {
//         value: "DRAFT",
//         label: "Draft",
//       },
//       {
//         value: "FAILED",
//         label: "Failed",
//       },
//     ],
//   };

//   return (
//     <Box
//       sx={{
//         width: "100%",
//       }}
//     >
//       {/* ========================================
//           PAGE HEADER
//       ======================================== */}

//       <CalendarHeader />

//       {/* ========================================
//           CALENDAR TOOLBAR
//       ======================================== */}

//       <CalendarToolbar
//         currentDate={currentDate}
//         search={search}
//         onPrevious={handlePrevious}
//         onNext={handleNext}
//         onToday={handleToday}
//         onDateChange={handleDateChange}
//         onSearchChange={handleSearchChange}
//         onFiltersChange={() => setFiltersOpen(true)}
//         activeFilterCount={activeFilterCount}
//       />

//       {/* ========================================
//           CALENDAR GRID
//       ======================================== */}

//       <Box
//         sx={{
//           mt: 2,
//         }}
//       >
//         <CalendarGrid
//           currentDate={currentDate}
//           search={search}
//           filters={appliedFilters}
//           onEventClick={handleEventClick}
//         />
//       </Box>

//       {/* ========================================
//           FILTER DRAWER
//       ======================================== */}

//       <CalendarFilters
//         open={filtersOpen}
//         onClose={() => setFiltersOpen(false)}
//         filters={filters}
//         onFilterChange={handleFilterChange}
//         onApply={handleApplyFilters}
//         onClear={handleClearFilters}
//         organizations={filterOptions.organizations}
//         platforms={filterOptions.platforms}
//         contentTypes={filterOptions.contentTypes}
//         statuses={filterOptions.statuses}
//       />

//       <CalendarEventDetails
//         open={eventDetailsOpen}
//         event={selectedEvent}
//         onClose={handleEventDetailsClose}
//       />
//     </Box>
//   );
// }

import { Box, CircularProgress, Typography } from "@mui/material";

import { useMemo, useState } from "react";

import dayjs from "dayjs";

import CalendarHeader from "../../components/calendar/CalendarHeader";
import CalendarToolbar from "../../components/calendar/CalendarToolbar";
import CalendarGrid from "../../components/calendar/CalendarGrid";
import CalendarFilters from "../../components/calendar/CalendarFilters";
import CalendarEventDetails from "../../components/calendar/event-details/CalendarEventDetails";

import useCalendar from "../../hooks/calendar/useCalendar";

import { DEFAULT_CALENDAR_FILTERS } from "../../constants/calendar/calendar.constants";

export default function Calendar() {
  // ==========================================
  // CURRENT CALENDAR DATE
  // ==========================================

  const [currentDate, setCurrentDate] = useState(dayjs());

  // ==========================================
  // SEARCH
  // ==========================================

  const [search, setSearch] = useState("");

  // ==========================================
  // FILTERS
  // ==========================================

  const [filters, setFilters] = useState(DEFAULT_CALENDAR_FILTERS);

  const [appliedFilters, setAppliedFilters] = useState(
    DEFAULT_CALENDAR_FILTERS,
  );

  // ==========================================
  // FILTER DRAWER
  // ==========================================

  const [filtersOpen, setFiltersOpen] = useState(false);

  // ==========================================
  // EVENT DETAILS
  // ==========================================

  const [selectedEvent, setSelectedEvent] = useState(null);

  const [eventDetailsOpen, setEventDetailsOpen] = useState(false);

  // ==========================================
  // CALENDAR DATA
  // ==========================================

  const {
    events,

    filterOptions,

    loading,

    filterOptionsLoading,

    error,

    filterOptionsError,

    refresh,
  } = useCalendar({
    currentDate,
    filters: appliedFilters,
    search,
  });

  // ==========================================
  // MONTH NAVIGATION
  // ==========================================

  function handlePrevious() {
    setCurrentDate((current) => current.subtract(1, "month"));
  }

  function handleNext() {
    setCurrentDate((current) => current.add(1, "month"));
  }

  function handleToday() {
    setCurrentDate(dayjs());
  }

  function handleDateChange(date) {
    if (!date) {
      return;
    }

    setCurrentDate(date);
  }

  // ==========================================
  // SEARCH
  // ==========================================

  function handleSearchChange(value) {
    setSearch(value);
  }

  // ==========================================
  // FILTER CHANGE
  // ==========================================

  function handleFilterChange(field, value) {
    setFilters((current) => ({
      ...current,
      [field]: value,
    }));
  }

  // ==========================================
  // APPLY FILTERS
  // ==========================================

  function handleApplyFilters() {
    setAppliedFilters({
      ...filters,
    });

    setFiltersOpen(false);
  }

  // ==========================================
  // CLEAR FILTERS
  // ==========================================

  function handleClearFilters() {
    const emptyFilters = {
      ...DEFAULT_CALENDAR_FILTERS,
    };

    setFilters(emptyFilters);

    setAppliedFilters(emptyFilters);
  }

  // ==========================================
  // ACTIVE FILTER COUNT
  // ==========================================

  const activeFilterCount = useMemo(() => {
    return Object.values(appliedFilters).filter(Boolean).length;
  }, [appliedFilters]);

  // ==========================================
  // EVENT DETAILS
  // ==========================================

  function handleEventClick(event) {
    setSelectedEvent(event);
    setEventDetailsOpen(true);
  }

  function handleEventDetailsClose() {
    setEventDetailsOpen(false);
    setSelectedEvent(null);
  }

  // ==========================================
  // RENDER
  // ==========================================

  return (
    <Box
      sx={{
        width: "100%",
      }}
    >
      {/* ========================================
          PAGE HEADER
      ======================================== */}

      <CalendarHeader />

      {/* ========================================
          CALENDAR TOOLBAR
      ======================================== */}

      <CalendarToolbar
        currentDate={currentDate}
        search={search}
        filters={appliedFilters}
        onPrevious={handlePrevious}
        onNext={handleNext}
        onToday={handleToday}
        onDateChange={handleDateChange}
        onSearchChange={handleSearchChange}
        onFiltersChange={() => setFiltersOpen(true)}
        activeFilterCount={activeFilterCount}
      />

      {/* ========================================
          CALENDAR CONTENT
      ======================================== */}

      <Box
        sx={{
          mt: 2,
          position: "relative",
        }}
      >
        {/* ======================================
            CALENDAR LOADING
        ====================================== */}

        {loading && (
          <Box
            sx={{
              minHeight: 300,

              display: "flex",

              alignItems: "center",

              justifyContent: "center",
            }}
          >
            <CircularProgress size={28} />
          </Box>
        )}

        {/* ======================================
            CALENDAR ERROR
        ====================================== */}

        {!loading && error && (
          <Box
            sx={{
              minHeight: 300,

              display: "flex",

              flexDirection: "column",

              alignItems: "center",

              justifyContent: "center",

              gap: 1,
            }}
          >
            <Typography
              sx={{
                fontWeight: 600,
                color: "text.primary",
              }}
            >
              Unable to load calendar
            </Typography>

            <Typography
              sx={{
                fontSize: 14,
                color: "text.secondary",
              }}
            >
              {error}
            </Typography>

            <Typography
              component="button"
              onClick={refresh}
              sx={{
                mt: 1,

                border: "none",

                bgcolor: "transparent",

                color: "primary.main",

                cursor: "pointer",

                fontWeight: 600,

                fontSize: 14,
              }}
            >
              Try again
            </Typography>
          </Box>
        )}

        {/* ======================================
            CALENDAR GRID
        ====================================== */}

        {!loading && !error && (
          <CalendarGrid
            currentDate={currentDate}
            events={events}
            filters={appliedFilters}
            onEventClick={handleEventClick}
          />
        )}
      </Box>

      {/* ========================================
          FILTER DRAWER
      ======================================== */}

      <CalendarFilters
        open={filtersOpen}
        onClose={() => setFiltersOpen(false)}
        filters={filters}
        onFilterChange={handleFilterChange}
        onApply={handleApplyFilters}
        onClear={handleClearFilters}
        organizations={filterOptions.organizations}
        platforms={filterOptions.platforms}
        contentTypes={filterOptions.contentTypes}
        statuses={filterOptions.statuses}
      />

      {/* ========================================
          EVENT DETAILS DRAWER
      ======================================== */}

      <CalendarEventDetails
        open={eventDetailsOpen}
        event={selectedEvent}
        onClose={handleEventDetailsClose}
      />
    </Box>
  );
}
