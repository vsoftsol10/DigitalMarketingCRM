import assert from "node:assert/strict";
import test from "node:test";

import formatApiErrorMessage from "./apiErrorMessage.js";

const rateLimitError = (retryAfter) => ({
  response: {
    status: 429,
    data: {
      success: false,
      message: "Request was throttled.",
      errors: { detail: "Request was throttled." },
    },
    headers: retryAfter === undefined ? {} : { "retry-after": retryAfter },
  },
});

test("429 errors include a readable delay from Retry-After seconds", () => {
  assert.equal(
    formatApiErrorMessage(rateLimitError("42")),
    "Too many requests. Please try again in 42 seconds.",
  );
});

test("429 errors remain useful when Retry-After is missing", () => {
  assert.equal(
    formatApiErrorMessage(rateLimitError()),
    "Too many requests. Please try again shortly.",
  );
});

test("429 errors safely fall back when Retry-After is malformed", () => {
  assert.equal(
    formatApiErrorMessage(rateLimitError("not-a-duration")),
    "Too many requests. Please try again shortly.",
  );
});
