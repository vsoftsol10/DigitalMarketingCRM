"""Endpoint-scoped, Redis-backed DRF rate limiting."""

import hashlib
import hmac
import logging
import math
import re

from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured
from rest_framework.exceptions import APIException
from rest_framework.throttling import BaseThrottle


logger = logging.getLogger(__name__)

_SCOPE_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{1,80}$")

# One EVAL increments every window counter for a request, so overlapping
# requests cannot race between separate GET/INCR/EXPIRE operations.
_INCREMENT_WINDOWS_SCRIPT = """
local result = {}
for index, key in ipairs(KEYS) do
    local count = redis.call('INCR', key)
    if count == 1 then
        redis.call('PEXPIRE', key, tonumber(ARGV[index]))
    end
    result[#result + 1] = count
    result[#result + 1] = redis.call('PTTL', key)
end
return result
"""


class RateLimitBackendUnavailable(APIException):
    status_code = 503
    default_detail = "Request limiting is temporarily unavailable. Please try again."
    default_code = "rate_limit_backend_unavailable"


class RedisRateThrottle(BaseThrottle):
    """Atomic fixed-window throttle intended for explicit per-view use.

    Subclasses should set ``scope``. Configure that scope in
    ``settings.DMC_RATE_LIMITS`` as a sequence of ``(request_count,
    window_seconds)`` pairs. Multiple windows are checked/incremented in one
    Redis script execution.
    """

    scope = None

    def __init__(self):
        self._retry_after = None
        self.remaining_requests = None

    def _configured_limits(self):
        scope = self.scope
        if not isinstance(scope, str) or not _SCOPE_PATTERN.fullmatch(scope):
            raise ImproperlyConfigured("A valid rate-limit scope is required.")

        configured = getattr(settings, "DMC_RATE_LIMITS", {}).get(scope)
        if not configured:
            raise ImproperlyConfigured(
                f"Rate-limit configuration is missing for scope '{scope}'."
            )

        limits = []
        for item in configured:
            if not isinstance(item, (tuple, list)) or len(item) != 2:
                raise ImproperlyConfigured(
                    f"Rate-limit scope '{scope}' has an invalid limit entry."
                )
            request_count, window_seconds = item
            if (
                isinstance(request_count, bool)
                or not isinstance(request_count, int)
                or request_count < 1
                or isinstance(window_seconds, bool)
                or not isinstance(window_seconds, int)
                or window_seconds < 1
            ):
                raise ImproperlyConfigured(
                    f"Rate-limit scope '{scope}' must use positive integer limits."
                )
            limits.append((request_count, window_seconds))

        if not limits:
            raise ImproperlyConfigured(
                f"Rate-limit configuration is missing for scope '{scope}'."
            )
        return limits

    def _subject_digest(self, request):
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            subject = f"user:{user.pk}"
        else:
            subject = f"ip:{self.get_ident(request)}"
        secret = str(settings.SECRET_KEY).encode("utf-8")
        return hmac.new(secret, subject.encode("utf-8"), hashlib.sha256).hexdigest()

    def _redis_client(self):
        """Return the configured default Redis cache client's write handle."""
        backend = caches["default"]
        if not hasattr(backend, "_cache") or not hasattr(backend._cache, "get_client"):
            raise RuntimeError("The configured default cache does not expose Redis.")
        return backend._cache.get_client(write=True)

    def _failure_policy(self):
        policy = getattr(settings, "DMC_RATE_LIMIT_REDIS_FAILURE_POLICY", "closed")
        if policy not in {"closed", "open"}:
            raise ImproperlyConfigured(
                "DMC_RATE_LIMIT_REDIS_FAILURE_POLICY must be 'closed' or 'open'."
            )
        return policy

    def allow_request(self, request, view):
        limits = self._configured_limits()
        digest = self._subject_digest(request)
        keys = [
            f"dmc:ratelimit:v1:{self.scope}:{digest}:{count}:{window_seconds}"
            for count, window_seconds in limits
        ]
        windows_ms = [window_seconds * 1000 for _, window_seconds in limits]

        try:
            values = self._redis_client().eval(
                _INCREMENT_WINDOWS_SCRIPT,
                len(keys),
                *keys,
                *windows_ms,
            )
            if not isinstance(values, (tuple, list)) or len(values) != 2 * len(limits):
                raise RuntimeError("Redis returned an invalid rate-limit result.")
            counts = [int(values[index * 2]) for index in range(len(limits))]
            ttls_ms = [int(values[index * 2 + 1]) for index in range(len(limits))]
        except Exception as exc:
            policy = self._failure_policy()
            # Avoid logging Redis exception text, which may contain connection
            # details. The policy and exception class are sufficient diagnostics.
            logger.error(
                "Redis rate limiting unavailable; policy=%s scope=%s error_type=%s",
                policy,
                self.scope,
                type(exc).__name__,
            )
            if policy == "open":
                return True
            raise RateLimitBackendUnavailable() from exc

        remaining = [limit - count for (limit, _), count in zip(limits, counts)]
        self.remaining_requests = max(0, min(remaining))
        exceeded_ttls = [
            max(0, ttl_ms)
            for (limit, _), count, ttl_ms in zip(limits, counts, ttls_ms)
            if count > limit
        ]
        if exceeded_ttls:
            # A request is allowed again only when every exceeded window has
            # reset, so use the longest remaining reset time.
            self._retry_after = max(1, math.ceil(max(exceeded_ttls) / 1000))
            return False

        self._retry_after = None
        return True

    def wait(self):
        return self._retry_after
