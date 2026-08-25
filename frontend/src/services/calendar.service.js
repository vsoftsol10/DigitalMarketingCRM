import calendarApi from "../api/calendar/calendar.api";

import {
  CALENDAR_EVENTS,
  CALENDAR_FILTER_OPTIONS,
} from "../data/calendar";

function normalizeCalendarEvent(event) {
  if (!event) {
    return null;
  }

  return {
    id: event.id,

    title: event.title || "",

    date: event.date || null,

    time: event.time || null,

    organization:
      event.organization || null,

    platform:
      event.platform || null,

    contentType:
      event.contentType ||
      event.content_type ||
      null,

    status:
      event.status || null,

    color:
      event.color || null,

    backgroundColor:
      event.backgroundColor ||
      event.background_color ||
      null,

    caption:
      event.caption || "",

    media: Array.isArray(event.media)
      ? event.media
      : [],

    timezone:
      event.timezone || null,

    createdAt:
      event.createdAt ||
      event.created_at ||
      null,

    updatedAt:
      event.updatedAt ||
      event.updated_at ||
      null,
  };
}

function filterMockEvents(
  events,
  params = {},
) {
  const {
    month,
    search,
    organization,
    platform,
    content_type,
    status,
  } = params;

  return events.filter((event) => {
    // ----------------------------------------
    // Month
    // ----------------------------------------

    if (
      month &&
      !event.date?.startsWith(month)
    ) {
      return false;
    }

    // ----------------------------------------
    // Search
    // ----------------------------------------

    if (search) {
      const query =
        search.toLowerCase();

      const searchableText = [
        event.title,
        event.caption,
        event.organization?.name,
        event.platform,
        event.contentType,
        event.status,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      if (
        !searchableText.includes(query)
      ) {
        return false;
      }
    }

    // ----------------------------------------
    // Organization
    // ----------------------------------------

    if (
      organization &&
      event.organization?.id !==
        organization
    ) {
      return false;
    }

    // ----------------------------------------
    // Platform
    // ----------------------------------------

    if (
      platform &&
      event.platform !== platform
    ) {
      return false;
    }

    // ----------------------------------------
    // Content Type
    // ----------------------------------------

    if (
      content_type &&
      event.contentType !==
        content_type
    ) {
      return false;
    }

    // ----------------------------------------
    // Status
    // ----------------------------------------

    if (
      status &&
      event.status !== status
    ) {
      return false;
    }

    return true;
  });
}

const calendarService = {
  // ==========================================
  // TEMPORARY MOCK MODE
  // ==========================================

  async getEvents(params = {}) {
    const filteredEvents =
      filterMockEvents(
        CALENDAR_EVENTS,
        params,
      );

    return filteredEvents
      .map(normalizeCalendarEvent)
      .filter(Boolean);
  },

  async getFilterOptions() {
    return CALENDAR_FILTER_OPTIONS;
  },

  async getEventById(eventId) {
    const event =
      CALENDAR_EVENTS.find(
        (item) =>
          item.id === eventId,
      );

    if (!event) {
      throw new Error(
        "Calendar event not found.",
      );
    }

    return normalizeCalendarEvent(event);
  },
};

export default calendarService;