const DEFAULT_FALLBACK = "Something went wrong. Please try again.";
const NETWORK_FALLBACK = "Unable to reach the server. Check your connection and try again.";
const SERVER_FALLBACK = "The server couldn't complete your request. Please try again later.";
const MAX_MESSAGE_LENGTH = 360;
const MAX_VALIDATION_MESSAGES = 4;

const UNSAFE_MESSAGE_PATTERN = /(?:traceback \(most recent call last\)|stack trace|internal server error|<!doctype html|<html\b|^\s*file ["'].*\.py|^[\w.]+(?:Error|Exception):|sqlstate|violates [\w ]*constraint|relation [\w." ]+ does not exist|column [\w." ]+ does not exist)/i;

function safeText(value) {
  if (typeof value !== "string") return "";

  const normalized = value.replace(/\s+/g, " ").trim();
  if (
    !normalized
    || normalized.toLowerCase() === "[object object]"
    || UNSAFE_MESSAGE_PATTERN.test(normalized)
  ) return "";

  return normalized.slice(0, MAX_MESSAGE_LENGTH);
}

function fieldLabel(field) {
  if (!field || field === "non_field_errors" || field === "detail") return "";

  return field
    .replace(/[_-]+/g, " ")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/^\w/, (letter) => letter.toUpperCase());
}

function collectValidationMessages(value, path = "", output = [], depth = 0) {
  if (output.length >= MAX_VALIDATION_MESSAGES || depth > 5) return output;

  if (typeof value === "string") {
    const message = safeText(value);
    if (message) {
      const label = fieldLabel(path.split(".").filter(Boolean).at(-1));
      output.push(label ? `${label}: ${message}` : message);
    }
    return output;
  }

  if (Array.isArray(value)) {
    value.forEach((item) => {
      if (output.length < MAX_VALIDATION_MESSAGES) {
        collectValidationMessages(item, path, output, depth + 1);
      }
    });
    return output;
  }

  if (value && typeof value === "object") {
    Object.entries(value).forEach(([key, nestedValue]) => {
      if (output.length < MAX_VALIDATION_MESSAGES) {
        collectValidationMessages(
          nestedValue,
          key === "non_field_errors" || key === "detail"
            ? path
            : [path, key].filter(Boolean).join("."),
          output,
          depth + 1,
        );
      }
    });
  }

  return output;
}

function getHeader(headers, name) {
  if (!headers) return "";

  if (typeof headers.get === "function") {
    return headers.get(name) || "";
  }

  const key = Object.keys(headers).find((headerName) => headerName.toLowerCase() === name.toLowerCase());
  return key ? headers[key] : "";
}

function retryAfterSeconds(headers) {
  const header = getHeader(headers, "Retry-After");
  if (header == null || header === "") return null;

  const seconds = Number(header);
  if (Number.isFinite(seconds) && seconds >= 0) return Math.ceil(seconds);

  const retryAt = Date.parse(String(header));
  if (!Number.isFinite(retryAt)) return null;

  return Math.max(0, Math.ceil((retryAt - Date.now()) / 1000));
}

function retryMessage(seconds) {
  if (seconds === 0) return "Too many requests. Please try again shortly.";
  return `Too many requests. Please try again in ${seconds} second${seconds === 1 ? "" : "s"}.`;
}

/** Convert common Django REST Framework/Axios failures into safe UI text. */
export function formatApiErrorMessage(error, { fallback = DEFAULT_FALLBACK } = {}) {
  const safeFallback = safeText(fallback) || DEFAULT_FALLBACK;
  const finalizeMessage = (message) => safeText(message) || safeFallback;

  if (typeof error === "string") {
    return finalizeMessage(error);
  }

  if (!error || typeof error !== "object") return finalizeMessage(safeFallback);

  const response = error.response;
  const status = Number(response?.status);
  const responseData = response?.data;

  if (status === 429) {
    const seconds = retryAfterSeconds(response?.headers);
    if (seconds !== null) return finalizeMessage(retryMessage(seconds));
    return finalizeMessage("Too many requests. Please try again shortly.");
  }

  if (status === 401) {
    return finalizeMessage("Your session may have expired. Please sign in again.");
  }

  if (status >= 500) return finalizeMessage(SERVER_FALLBACK);

  const apiMessage = safeText(responseData?.message)
    || safeText(responseData?.detail);
  const validationMessages = collectValidationMessages(responseData?.errors);

  if (validationMessages.length) {
    const validationText = validationMessages.join(" ");
    if (!apiMessage || apiMessage.toLowerCase() === "validation error") {
      return finalizeMessage(validationText);
    }
    return finalizeMessage(`${apiMessage} ${validationText}`);
  }

  if (apiMessage && apiMessage.toLowerCase() !== "validation error") {
    return finalizeMessage(apiMessage);
  }

  if (!response && (error.request || error.code === "ERR_NETWORK" || error.code === "ECONNABORTED")) {
    return finalizeMessage(NETWORK_FALLBACK);
  }

  return finalizeMessage(error.message);
}

export default formatApiErrorMessage;
