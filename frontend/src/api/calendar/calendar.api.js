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
   * GET /posts/calendar/events/
   */
  async getEvents(params = {}, { signal } = {}) {
    const response = await api.get(
      "/posts/calendar/events/",
      {
        params,
        signal,
      },
    );

    return response.data;
  },

  /**
   * Fetch calendar filter options.
   *
   * Backend:
   * GET /posts/calendar/filters/
   */
  async getFilterOptions() {
    const response = await api.get(
      "/posts/calendar/filters/",
    );

    return response.data;
  },

  /**
   * Fetch a single calendar event.
   *
   * Backend:
   * GET /posts/calendar/events/<target_id>/
   */
  async getEventById(eventId) {
    const response = await api.get(
      `/posts/calendar/events/${eventId}/`,
    );

    return response.data;
  },
};

export default calendarApi;
