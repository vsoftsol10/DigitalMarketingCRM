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

import { useEffect, useMemo, useState } from "react";

import dayjs from "dayjs";
import toast from "react-hot-toast";
import { useLocation, useNavigate } from "react-router-dom";

import CalendarHeader from "../../components/calendar/CalendarHeader";
import CalendarToolbar from "../../components/calendar/CalendarToolbar";
import CalendarGrid from "../../components/calendar/CalendarGrid";
import CalendarFilters from "../../components/calendar/CalendarFilters";
import CalendarEventDetails from "../../components/calendar/event-details/CalendarEventDetails";
import CalendarScheduleDialog from "../../components/calendar/event-details/CalendarScheduleDialog";
import ConfirmDialog from "../../components/ui/dialog/ConfirmDialog";

import useCalendar from "../../hooks/calendar/useCalendar";
import calendarService from "../../services/calendar.service";
import postService from "../../services/post.service";

import { DEFAULT_CALENDAR_FILTERS } from "../../constants/calendar/calendar.constants";

export default function Calendar() {
  const location = useLocation();
  const navigate = useNavigate();
  const calendarTargetId = location.state?.targetId;

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

  const [actionLoading, setActionLoading] = useState(false);

  const [confirmation, setConfirmation] = useState(null);

  const [scheduleEvent, setScheduleEvent] = useState(null);

  // ==========================================
  // CALENDAR DATA
  // ==========================================

  const {
    events,

    filterOptions,

    loading,

    isInitialLoading,

    isRefreshing,

    filterOptionsLoading,

    error,

    filterOptionsError,

    refresh,
  } = useCalendar({
    currentDate,
    filters: appliedFilters,
    search,
  });

  useEffect(() => {
    if (!calendarTargetId) {
      return undefined;
    }

    let isActive = true;

    async function openCalendarTarget() {
      try {
        const event = await calendarService.getEventById(calendarTargetId);

        if (!isActive || !event) {
          return;
        }

        setSelectedEvent(event);
        setEventDetailsOpen(true);
      } catch (targetError) {
        if (!isActive) {
          return;
        }

        toast.error(
          targetError?.response?.status === 404
            ? "The selected calendar event is no longer available."
            : "Unable to open the selected calendar event.",
        );
      } finally {
        if (isActive) {
          navigate(
            `${location.pathname}${location.search}${location.hash}`,
            { replace: true, state: null },
          );
        }
      }
    }

    openCalendarTarget();

    return () => {
      isActive = false;
    };
  }, [
    calendarTargetId,
    location.hash,
    location.pathname,
    location.search,
    navigate,
  ]);

  useEffect(() => {
    if (!selectedEvent) {
      return;
    }

    const refreshedEvent = events.find(
      (event) => (event.targetId || event.id) === (selectedEvent.targetId || selectedEvent.id),
    );

    if (refreshedEvent) {
      setSelectedEvent(refreshedEvent);
    }
  }, [events, selectedEvent]);

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

  function getEventIdentifiers(event) {
    const organizationId = event?.organizationId || event?.organization?.id;
    const postId = event?.postId;
    const targetId = event?.targetId || event?.id;

    if (!organizationId || !postId) {
      throw new Error("This calendar event is missing its post details.");
    }

    return { organizationId, postId, targetId };
  }

  function getActionErrorMessage(actionError, fallback) {
    return (
      actionError?.response?.data?.message ||
      actionError?.response?.data?.detail ||
      actionError?.message ||
      fallback
    );
  }

  async function refreshEvent(event) {
    const refreshedEvents = await refresh();
    const refreshedEvent = refreshedEvents?.find(
      (candidate) => candidate.id === event.id,
    );

    if (refreshedEvent) {
      setSelectedEvent(refreshedEvent);
    }
  }

  async function runAction(action, fallbackMessage) {
    if (actionLoading) {
      return false;
    }

    try {
      setActionLoading(true);
      await action();
      return true;
    } catch (actionError) {
      toast.error(getActionErrorMessage(actionError, fallbackMessage));
      return false;
    } finally {
      setActionLoading(false);
    }
  }

  function handleSchedule(event) {
    setScheduleEvent(event);
  }

  async function handleScheduleConfirm(values) {
    const event = scheduleEvent;
    if (!event) {
      return;
    }

    const succeeded = await runAction(async () => {
      const { organizationId, postId, targetId } = getEventIdentifiers(event);
      const response = await postService.schedulePostTarget(
        organizationId,
        postId,
        targetId,
        values,
      );

      if (!response?.success) {
        throw new Error(response?.message || "Unable to schedule the post.");
      }

      await refreshEvent(event);
      toast.success(
        response.message ||
          (event.status?.toUpperCase() === "SCHEDULED"
            ? "Post rescheduled successfully."
            : "Post scheduled successfully."),
      );
    }, "Unable to schedule the post.");

    if (succeeded) {
      setScheduleEvent(null);
    }
  }

  function handleDeleteRequest(event) {
    setConfirmation({ type: "delete", event });
  }

  function handlePublishNowRequest(event) {
    setConfirmation({ type: "publish", event });
  }

  async function handleConfirmation() {
    const pendingConfirmation = confirmation;
    if (!pendingConfirmation) {
      return;
    }

    const { event, type } = pendingConfirmation;
    const succeeded = await runAction(async () => {
      const { organizationId, postId, targetId } = getEventIdentifiers(event);
      const response = type === "delete"
        ? await postService.deletePostTarget(organizationId, postId, targetId)
        : await postService.publishPostTargetNow(
          organizationId,
          postId,
          targetId,
        );

      if (!response?.success) {
        throw new Error(
          response?.message ||
            (type === "delete"
              ? "Unable to delete the post."
              : "Unable to publish the post now."),
        );
      }

      if (type === "delete") {
        handleEventDetailsClose();
        await refresh();
        toast.success(response.message || "Post deleted successfully.");
        return;
      }

      await refreshEvent(event);
      toast.success(response.message || "Post queued for publishing.");
    }, type === "delete" ? "Unable to delete the post." : "Unable to publish the post now.");

    if (succeeded) {
      setConfirmation(null);
    }
  }

  async function handleRetry(event) {
    await runAction(async () => {
      const { organizationId, postId, targetId } = getEventIdentifiers(event);
      const response = await postService.retryPostTarget(
        organizationId,
        postId,
        targetId,
      );

      if (!response?.success) {
        throw new Error(response?.message || "Unable to retry publishing.");
      }

      await refreshEvent(event);
      toast.success(response.message || "Publishing retry queued.");
    }, "Unable to retry publishing.");
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

        {isInitialLoading && (
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

        {!isInitialLoading && error && !events.length && (
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

        {!isInitialLoading && (!error || events.length > 0) && (
          <CalendarGrid
            currentDate={currentDate}
            events={events}
            filters={appliedFilters}
            onEventClick={handleEventClick}
          />
        )}

        {isRefreshing && (
          <Box
            sx={{
              position: "absolute",
              top: 8,
              right: 8,
              zIndex: 2,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 28,
              height: 28,
              borderRadius: "50%",
              bgcolor: "background.paper",
              boxShadow: "0 1px 4px rgba(15, 23, 42, 0.12)",
            }}
          >
            <CircularProgress size={16} />
          </Box>
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
        socialAccounts={filterOptions.socialAccounts}
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
        onReschedule={handleSchedule}
        onPublishNow={handlePublishNowRequest}
        onRetry={handleRetry}
        onDelete={handleDeleteRequest}
        actionLoading={actionLoading}
      />

      <CalendarScheduleDialog
        open={Boolean(scheduleEvent)}
        event={scheduleEvent}
        loading={actionLoading}
        onClose={() => setScheduleEvent(null)}
        onConfirm={handleScheduleConfirm}
      />

      <ConfirmDialog
        open={Boolean(confirmation)}
        title={
          confirmation?.type === "delete"
            ? "Delete post"
            : "Publish post now"
        }
        message={
          confirmation?.type === "delete"
            ? "Are you sure you want to delete"
            : "Are you sure you want to publish"
        }
        entityName={confirmation?.event?.title || "this post"}
        description={
          confirmation?.type === "delete"
            ? "This action cannot be undone."
            : "It will be queued for publishing immediately."
        }
        confirmText={
          confirmation?.type === "delete" ? "Delete" : "Publish now"
        }
        loading={actionLoading}
        onClose={() => {
          if (!actionLoading) {
            setConfirmation(null);
          }
        }}
        onConfirm={handleConfirmation}
      />
    </Box>
  );
}
