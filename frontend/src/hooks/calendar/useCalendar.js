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
  useRef,
  useState,
} from "react";

import calendarService from "../../services/calendar.service";

function useDebouncedValue(value, delay = 600) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => setDebouncedValue(value), delay);
    return () => window.clearTimeout(timeoutId);
  }, [value, delay]);

  return debouncedValue;
}

function areCalendarValuesEqual(left, right) {
  if (Object.is(left, right)) {
    return true;
  }

  if (!left || !right || typeof left !== "object" || typeof right !== "object") {
    return false;
  }

  if (Array.isArray(left) !== Array.isArray(right)) {
    return false;
  }

  const leftKeys = Object.keys(left);
  const rightKeys = Object.keys(right);

  return leftKeys.length === rightKeys.length
    && leftKeys.every((key) => (
      Object.prototype.hasOwnProperty.call(right, key)
      && areCalendarValuesEqual(left[key], right[key])
    ));
}

function areCalendarEventListsEqual(currentEvents, nextEvents) {
  return currentEvents.length === nextEvents.length
    && currentEvents.every((event, index) => (
      areCalendarValuesEqual(event, nextEvents[index])
    ));
}

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
      socialAccounts: [],
      contentTypes: [],
      statuses: [],
    });

  // ==========================================
  // LOADING
  // ==========================================

  const [loading, setLoading] = useState(false);

  const [backgroundSyncing, setBackgroundSyncing] = useState(false);

  const [hasLoadedEvents, setHasLoadedEvents] = useState(false);

  const eventRequestRef = useRef({
    id: 0,
    controller: null,
    promise: null,
    kind: null,
    scope: null,
  });
  const debouncedSearch = useDebouncedValue(search.trim());

  const [isCalendarVisible, setIsCalendarVisible] = useState(
    () => typeof document === "undefined" || document.visibilityState !== "hidden",
  );
  const [isBrowserOnline, setIsBrowserOnline] = useState(
    () => typeof navigator === "undefined" || navigator.onLine,
  );

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

  const fetchEvents = useCallback(({
    background = false,
    coalesce = false,
  } = {}) => {
    const params = {
      month: currentDate?.format("YYYY-MM"),
      search: debouncedSearch || undefined,
      organization: filters.organization || undefined,
      social_account: filters.socialAccount || undefined,
      content_type: filters.contentType || undefined,
      status: filters.status || undefined,
    };
    const requestScope = JSON.stringify(params);
    const activeRequest = eventRequestRef.current;

    if (background && coalesce && activeRequest.controller) {
      if (activeRequest.kind === "foreground" || activeRequest.scope === requestScope) {
        return activeRequest.promise;
      }
    }

    activeRequest.controller?.abort();
    const controller = new AbortController();
    const requestId = activeRequest.id + 1;

    eventRequestRef.current = {
      id: requestId,
      controller,
      promise: null,
      kind: background ? "background" : "foreground",
      scope: requestScope,
    };

    if (background) {
      setBackgroundSyncing(true);
    } else {
      setBackgroundSyncing(false);
      setLoading(true);
    }
    setError(null);

    const request = (async () => {
      try {
        const data = await calendarService.getEvents(params, {
          signal: controller.signal,
        });

        if (eventRequestRef.current.id !== requestId) {
          return;
        }

        const nextEvents = Array.isArray(data) ? data : [];
        setEvents((currentEvents) => (
          areCalendarEventListsEqual(currentEvents, nextEvents)
            ? currentEvents
            : nextEvents
        ));
        setHasLoadedEvents(true);
        return nextEvents;
      } catch (err) {
        if (controller.signal.aborted || eventRequestRef.current.id !== requestId) {
          return;
        }

        console.error("Failed to fetch calendar events:", err);
        setError(
          err?.response?.data?.detail ||
            err?.message ||
            "Unable to load calendar events.",
        );
      } finally {
        if (eventRequestRef.current.id === requestId) {
          eventRequestRef.current = {
            id: requestId,
            controller: null,
            promise: null,
            kind: null,
            scope: null,
          };
          setLoading(false);
          setBackgroundSyncing(false);
        }
      }
    })();

    eventRequestRef.current.promise = request;
    return request;
  }, [
    currentDate,
    filters.organization,
    filters.socialAccount,
    filters.contentType,
    filters.status,
    debouncedSearch,
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

          socialAccounts:
            Array.isArray(data?.social_accounts)
              ? data.social_accounts
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
          socialAccounts: [],
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
    return () => {
      const activeRequest = eventRequestRef.current;
      activeRequest.controller?.abort();
      eventRequestRef.current = {
        id: activeRequest.id + 1,
        controller: null,
        promise: null,
        kind: null,
        scope: null,
      };
    };
  }, [fetchEvents]);

  const pollingInterval = events.some(
    (event) => event.status?.toUpperCase() === "PUBLISHING",
  )
    ? 15000
    : events.some((event) => event.status?.toUpperCase() === "SCHEDULED")
      ? 30000
      : null;

  useEffect(() => {
    if (!pollingInterval || !isCalendarVisible || !isBrowserOnline) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      fetchEvents({ background: true, coalesce: true });
    }, pollingInterval);
    return () => window.clearInterval(intervalId);
  }, [fetchEvents, isBrowserOnline, isCalendarVisible, pollingInterval]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      const isVisible = document.visibilityState !== "hidden";
      setIsCalendarVisible(isVisible);

      if (isVisible) {
        fetchEvents({ background: true, coalesce: true });
      }
    };

    const handleOnline = () => {
      setIsBrowserOnline(true);
      if (document.visibilityState !== "hidden") {
        fetchEvents({ background: true, coalesce: true });
      }
    };

    const handleOffline = () => setIsBrowserOnline(false);

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [fetchEvents]);

  // ==========================================
  // REFRESH EVENTS
  // ==========================================

  const refresh = useCallback(() => {
    return fetchEvents();
  }, [fetchEvents]);

  const removeEvent = useCallback((targetId) => {
    setEvents((currentEvents) => currentEvents.filter(
      (event) => (event.targetId || event.id) !== targetId,
    ));
  }, []);

  const syncEvent = useCallback((updatedEvent) => {
    if (!updatedEvent) {
      return;
    }

    const targetId = updatedEvent.targetId || updatedEvent.id;
    if (!targetId) {
      return;
    }

    const matchesCurrentView = (
      (!currentDate || updatedEvent.date?.slice(0, 7) === currentDate.format("YYYY-MM"))
      && (!filters.organization || updatedEvent.organizationId === filters.organization)
      && (!filters.socialAccount || updatedEvent.socialAccountId === filters.socialAccount)
      && (!filters.contentType || updatedEvent.contentType?.toUpperCase() === filters.contentType.toUpperCase())
      && (!filters.status || updatedEvent.status?.toUpperCase() === filters.status.toUpperCase())
    );

    setEvents((currentEvents) => {
      const wasInCurrentCollection = currentEvents.some(
        (event) => (event.targetId || event.id) === targetId,
      );
      const withoutTarget = currentEvents.filter(
        (event) => (event.targetId || event.id) !== targetId,
      );

      if (!wasInCurrentCollection || !matchesCurrentView) {
        return withoutTarget;
      }

      return [...withoutTarget, updatedEvent];
    });
  }, [
    currentDate,
    filters.contentType,
    filters.organization,
    filters.socialAccount,
    filters.status,
  ]);

  // ==========================================
  // RETURN
  // ==========================================

  return {
    events,

    filterOptions,

    loading,

    isInitialLoading: (loading || backgroundSyncing) && !hasLoadedEvents,

    isRefreshing: loading && hasLoadedEvents,

    isBackgroundSyncing: backgroundSyncing && hasLoadedEvents,

    filterOptionsLoading,

    error,

    filterOptionsError,

    refresh,
    removeEvent,
    syncEvent,
  };
}
