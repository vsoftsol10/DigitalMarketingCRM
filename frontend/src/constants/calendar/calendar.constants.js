// ==========================================
// CALENDAR DAYS
// ==========================================

export const CALENDAR_WEEK_DAYS = [
  "Sun",
  "Mon",
  "Tue",
  "Wed",
  "Thu",
  "Fri",
  "Sat",
];

// ==========================================
// CALENDAR POST STATUS
// ==========================================

export const CALENDAR_POST_STATUS = {
  DRAFT: "DRAFT",
  SCHEDULED: "SCHEDULED",
  PUBLISHING: "PUBLISHING",
  UNRESOLVED: "UNRESOLVED",
  PUBLISHED: "PUBLISHED",
  FAILED: "FAILED",
};

// ==========================================
// CALENDAR PLATFORMS
// ==========================================
//
// These are domain-level platform identifiers.
// Actual platform data will come from the backend.

export const CALENDAR_PLATFORM = {
  INSTAGRAM: "INSTAGRAM",
  FACEBOOK: "FACEBOOK",
  LINKEDIN: "LINKEDIN",
  YOUTUBE: "YOUTUBE",
  THREADS: "THREADS",
  X: "X",
};

// ==========================================
// CALENDAR CONTENT TYPES
// ==========================================

export const CALENDAR_CONTENT_TYPE = {
  POST: "POST",
  REEL: "REEL",
  STORY: "STORY",
  CAROUSEL: "CAROUSEL",
  VIDEO: "VIDEO",
  SHORT: "SHORT",
};

// ==========================================
// CALENDAR VIEW
// ==========================================
//
// Currently we are building the Month view.
// Keeping this as a domain constant makes it
// easier to extend later.

export const CALENDAR_VIEW = {
  MONTH: "MONTH",
};

// ==========================================
// DEFAULT CALENDAR FILTERS
// ==========================================

export const DEFAULT_CALENDAR_FILTERS = {
  organization: "",
  socialAccount: "",
  contentType: "",
  status: "",
};
