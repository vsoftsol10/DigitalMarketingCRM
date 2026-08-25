// import { useCallback, useEffect, useState } from "react";

// import calendarService from "../../services/calendar.service";

// export default function useCalendar({
//   currentDate,
//   filters = {},
//   search = "",
// } = {}) {
//   // ==========================================
//   // EVENTS
//   // ==========================================

//   const [events, setEvents] = useState([]);

//   // ==========================================
//   // LOADING
//   // ==========================================

//   const [loading, setLoading] = useState(false);

//   // ==========================================
//   // ERROR
//   // ==========================================

//   const [error, setError] = useState(null);

//   // ==========================================
//   // FETCH CALENDAR EVENTS
//   // ==========================================

//   const fetchEvents = useCallback(async () => {
//     setLoading(true);
//     setError(null);

//     try {
//       const params = {
//         month: currentDate?.format("YYYY-MM"),
//         search: search || undefined,

//         organization:
//           filters.organization || undefined,

//         platform:
//           filters.platform || undefined,

//         content_type:
//           filters.contentType || undefined,

//         status:
//           filters.status || undefined,
//       };

//       const data =
//         await calendarService.getEvents(params);

//       setEvents(data);
//     } catch (err) {
//       console.error(
//         "Failed to fetch calendar events:",
//         err,
//       );

//       setEvents([]);

//       setError(
//         err?.response?.data?.detail ||
//           err?.message ||
//           "Unable to load calendar events.",
//       );
//     } finally {
//       setLoading(false);
//     }
//   }, [
//     currentDate,
//     filters.organization,
//     filters.platform,
//     filters.contentType,
//     filters.status,
//     search,
//   ]);

//   // ==========================================
//   // FETCH WHEN CALENDAR STATE CHANGES
//   // ==========================================

//   useEffect(() => {
//     fetchEvents();
//   }, [fetchEvents]);

//   // ==========================================
//   // REFRESH
//   // ==========================================

//   const refresh = useCallback(() => {
//     return fetchEvents();
//   }, [fetchEvents]);

//   // ==========================================
//   // RETURN
//   // ==========================================

//   return {
//     events,
//     loading,
//     error,
//     refresh,
//   };
// }

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import calendarService from "../../services/calendar.service";

export default function useCalendar({
  currentDate,
  filters = {},
  search = "",
} = {}) {
  // ==========================================
  // EVENTS
  // ==========================================

  const [events, setEvents] = useState([]);

  // ==========================================
  // FILTER OPTIONS
  // ==========================================

  const [filterOptions, setFilterOptions] =
    useState({
      organizations: [],
      platforms: [],
      contentTypes: [],
      statuses: [],
    });

  // ==========================================
  // LOADING
  // ==========================================

  const [loading, setLoading] = useState(false);

  const [filterOptionsLoading, setFilterOptionsLoading] =
    useState(false);

  // ==========================================
  // ERROR
  // ==========================================

  const [error, setError] = useState(null);

  const [filterOptionsError, setFilterOptionsError] =
    useState(null);

  // ==========================================
  // FETCH CALENDAR EVENTS
  // ==========================================

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = {
        month: currentDate?.format("YYYY-MM"),

        search: search || undefined,

        organization:
          filters.organization || undefined,

        platform:
          filters.platform || undefined,

        content_type:
          filters.contentType || undefined,

        status:
          filters.status || undefined,
      };

      const data =
        await calendarService.getEvents(params);

      setEvents(
        Array.isArray(data)
          ? data
          : []
      );
    } catch (err) {
      console.error(
        "Failed to fetch calendar events:",
        err
      );

      setEvents([]);

      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Unable to load calendar events."
      );
    } finally {
      setLoading(false);
    }
  }, [
    currentDate,
    filters.organization,
    filters.platform,
    filters.contentType,
    filters.status,
    search,
  ]);

  // ==========================================
  // FETCH FILTER OPTIONS
  // ==========================================

  const fetchFilterOptions =
    useCallback(async () => {
      setFilterOptionsLoading(true);
      setFilterOptionsError(null);

      try {
        const data =
          await calendarService.getFilterOptions();

        setFilterOptions({
          organizations:
            Array.isArray(data?.organizations)
              ? data.organizations
              : [],

          platforms:
            Array.isArray(data?.platforms)
              ? data.platforms
              : [],

          contentTypes:
            Array.isArray(data?.contentTypes)
              ? data.contentTypes
              : [],

          statuses:
            Array.isArray(data?.statuses)
              ? data.statuses
              : [],
        });
      } catch (err) {
        console.error(
          "Failed to fetch calendar filter options:",
          err
        );

        setFilterOptions({
          organizations: [],
          platforms: [],
          contentTypes: [],
          statuses: [],
        });

        setFilterOptionsError(
          err?.response?.data?.detail ||
            err?.message ||
            "Unable to load calendar filter options."
        );
      } finally {
        setFilterOptionsLoading(false);
      }
    }, []);

  // ==========================================
  // INITIAL FILTER OPTIONS
  // ==========================================

  useEffect(() => {
    fetchFilterOptions();
  }, [fetchFilterOptions]);

  // ==========================================
  // FETCH EVENTS WHEN STATE CHANGES
  // ==========================================

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  // ==========================================
  // REFRESH EVENTS
  // ==========================================

  const refresh = useCallback(() => {
    return fetchEvents();
  }, [fetchEvents]);

  // ==========================================
  // RETURN
  // ==========================================

  return {
    events,

    filterOptions,

    loading,

    filterOptionsLoading,

    error,

    filterOptionsError,

    refresh,
  };
}