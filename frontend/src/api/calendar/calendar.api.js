import api from "../axios";

/**
 * Calendar API
 *
 * Responsible only for communicating
 * with the calendar backend endpoints.
 */

const calendarApi = {
  /**
   * Fetch calendar events.
   *
   * Backend:
   * GET /calendar/events/
   */
  async getEvents(params = {}) {
    const response = await api.get(
      "/calendar/events/",
      {
        params,
      },
    );

    return response.data;
  },

  /**
   * Fetch calendar filter options.
   *
   * Backend:
   * GET /calendar/filters/
   */
  async getFilterOptions() {
    const response = await api.get(
      "/calendar/filters/",
    );

    return response.data;
  },

  /**
   * Fetch a single calendar event.
   *
   * Backend:
   * GET /calendar/events/:id/
   */
  async getEventById(eventId) {
    const response = await api.get(
      `/calendar/events/${eventId}/`,
    );

    return response.data;
  },
};

export default calendarApi;