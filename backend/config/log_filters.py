"""Logging filters for credential-bearing HTTP diagnostics."""

import logging
import re


class CredentialRedactionFilter(logging.Filter):
    """Redact credentials from low-level HTTP library log records."""

    _SECRET_ASSIGNMENT = re.compile(
        r"(?i)(\b(?:access_token|refresh_token)\s*[=:]\s*)[^\s&,'\";]+"
    )
    _AUTHORIZATION = re.compile(
        r"(?i)(\b(?:proxy-)?authorization\s*[:=]\s*)"
        r"(?:(?:bearer|basic)\s+)?[^\s,;'\"]+"
    )
    _BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+=*")
    _COOKIE = re.compile(
        r"(?i)(\b(?:cookie|set-cookie)\s*[:=]\s*)[^\r\n]+"
    )

    @classmethod
    def _redact(cls, value):
        value = cls._SECRET_ASSIGNMENT.sub(r"\1[redacted]", value)
        value = cls._AUTHORIZATION.sub(r"\1[redacted]", value)
        value = cls._BEARER.sub("Bearer [redacted]", value)
        return cls._COOKIE.sub(r"\1[redacted]", value)

    def filter(self, record):
        try:
            record.msg = self._redact(record.getMessage())
            record.args = ()
            if record.exc_info:
                formatted_exception = logging.Formatter().formatException(record.exc_info)
                record.exc_text = self._redact(formatted_exception)
                record.exc_info = None
        except Exception:
            # If rendering fails, suppress this HTTP diagnostic rather than risk
            # emitting an unredacted credential-bearing value.
            record.msg = "HTTP diagnostic suppressed by credential redaction filter"
            record.args = ()
            record.exc_info = None
            record.exc_text = None
        return True
