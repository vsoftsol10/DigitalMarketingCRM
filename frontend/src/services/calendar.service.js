import calendarApi from "../api/calendar/calendar.api";

function normalizeCalendarEvent(event) {
  if (!event) {
    return null;
  }

  return {
    id: event.id,

    targetId: event.target_id || event.targetId || event.id,

    target_id: event.target_id || event.targetId || event.id,

    postId: event.post_id || event.postId || null,

    post_id: event.post_id || event.postId || null,

    organizationId:
      event.organization_id ||
      event.organizationId ||
      event.organization?.id ||
      null,

    organization_id:
      event.organization_id ||
      event.organizationId ||
      event.organization?.id ||
      null,

    title: event.title || "",

    date: event.date || null,

    time: event.time || null,

    organization:
      event.organization || null,

    platform: event.platform || null,

    socialAccount:
      event.social_account || event.socialAccount || null,

    socialAccountId:
      event.social_account_id ||
      event.socialAccountId ||
      event.social_account?.id ||
      event.socialAccount?.id ||
      null,

    social_account_id:
      event.social_account_id ||
      event.socialAccountId ||
      event.social_account?.id ||
      event.socialAccount?.id ||
      null,

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

    media: Array.isArray(event.media) ? event.media : [],

    errorMessage: event.error_message || event.errorMessage || "",

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

const calendarService = {
  async getEvents(params = {}, { signal } = {}) {
    const response = await calendarApi.getEvents(params, { signal });
    if (response?.success !== true || !Array.isArray(response.data)) {
      throw new Error("Calendar events were not returned in the expected format.");
    }

    const hasMalformedEvent = response.data.some((event) => (
      !event
      || typeof event !== "object"
      || Array.isArray(event)
      || typeof event.id !== "string"
      || !event.id.trim()
      || typeof event.platform !== "string"
      || !event.platform.trim()
    ));

    if (hasMalformedEvent) {
      throw new Error("Calendar events included an invalid event entry.");
    }

    return response.data
      .map(normalizeCalendarEvent);
  },

  async getFilterOptions() {
    const response = await calendarApi.getFilterOptions();
    return response?.data || {};
  },

  async getEventById(eventId) {
    const response = await calendarApi.getEventById(eventId);
    return normalizeCalendarEvent(response?.data);
  },
};

export default calendarService;
