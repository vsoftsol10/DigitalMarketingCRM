import logging
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.social_accounts.models import (
    SocialAccountStatus,
)

from .client import InstagramAPIClient
from .crypto import decrypt_token, encrypt_token
from .exceptions import (
    InstagramAPIError,
    InstagramIntegrationError,
)
from .models import (
    InstagramAccountCredential,
    InstagramCredentialStatus,
)

logger = logging.getLogger(__name__)


# ============================================================
# DEFAULTS
# ============================================================

DEFAULT_REFRESH_WINDOW = timedelta(days=7)

# Redis distributed lock.
#
# Only one worker should refresh the same credential at a time.
REFRESH_LOCK_TIMEOUT_SECONDS = 5 * 60


class InstagramTokenLifecycleService:
    """
    Production service responsible for maintaining Instagram
    long-lived access tokens.

    Responsibilities:
        - Detect credentials approaching expiry.
        - Refresh tokens before expiry.
        - Encrypt and persist refreshed tokens.
        - Update token expiry.
        - Synchronize SocialAccount health state.
        - Detect provider-invalid/revoked tokens.
        - Prevent concurrent refresh operations.

    OAuth login/reconnection is intentionally handled by
    services.py and is NOT handled here.
    """

    def __init__(self):
        self.client = InstagramAPIClient()

    # ========================================================
    # REFRESH WINDOW
    # ========================================================

    @staticmethod
    def get_refresh_window():
        """
        Return the configured token refresh window.

        Default:
            7 days before token expiry.
        """

        seconds = getattr(
            settings,
            "INSTAGRAM_TOKEN_REFRESH_WINDOW_SECONDS",
            int(DEFAULT_REFRESH_WINDOW.total_seconds()),
        )

        try:
            seconds = int(seconds)
        except (TypeError, ValueError):
            seconds = int(DEFAULT_REFRESH_WINDOW.total_seconds())

        return timedelta(
            seconds=max(seconds, 0),
        )

    # ========================================================
    # DUE CHECK
    # ========================================================

    @classmethod
    def credential_needs_refresh(
        cls,
        credential,
        *,
        now=None,
    ):
        """
        Determine whether an ACTIVE credential requires refresh.

        Rules:

            REVOKED / EXPIRED / ERROR
                -> False

            ACTIVE + expiry missing
                -> True

            ACTIVE + already expired
                -> True

            ACTIVE + expiry within refresh window
                -> True

            ACTIVE + expiry outside refresh window
                -> False
        """

        if credential.status != InstagramCredentialStatus.ACTIVE:
            return False

        now = now or timezone.now()

        expires_at = credential.token_expires_at

        # An ACTIVE credential without expiry needs attention.
        #
        # The provider will return the authoritative expiry during
        # refresh.
        if expires_at is None:
            return True

        refresh_deadline = now + cls.get_refresh_window()

        return expires_at <= refresh_deadline

    # ========================================================
    # SINGLE CREDENTIAL REFRESH
    # ========================================================

    def refresh_credential(
        self,
        credential_id,
    ):
        """
        Refresh a single Instagram credential.

        Redis locking prevents multiple workers from refreshing
        the same credential concurrently.
        """

        lock_key = f"instagram:token-refresh:{credential_id}"

        lock_acquired = cache.add(
            lock_key,
            "1",
            timeout=REFRESH_LOCK_TIMEOUT_SECONDS,
        )

        if not lock_acquired:
            return {
                "status": "locked",
                "credential_id": str(credential_id),
            }

        try:
            return self._refresh_credential_locked(
                credential_id,
            )

        finally:
            cache.delete(lock_key)

    # ========================================================
    # LOCKED REFRESH
    # ========================================================

    def _refresh_credential_locked(
        self,
        credential_id,
    ):
        """
        Actual refresh implementation.

        Redis lock has already been acquired before entering
        this method.
        """

        credential = (
            InstagramAccountCredential.objects.select_related("social_account")
            .filter(
                id=credential_id,
                is_deleted=False,
            )
            .first()
        )

        if credential is None:
            logger.warning(
                "Instagram credential %s was not found.",
                credential_id,
            )

            return {
                "status": "not_found",
                "credential_id": str(credential_id),
            }

        # ----------------------------------------------------
        # NEVER AUTO-RESTORE MANUALLY REVOKED CREDENTIALS
        # ----------------------------------------------------

        if credential.status == InstagramCredentialStatus.REVOKED:
            logger.info(
                "Skipping manually revoked Instagram " "credential %s.",
                credential_id,
            )

            return {
                "status": "revoked",
                "credential_id": str(credential_id),
            }

        # Only ACTIVE credentials participate in automatic
        # lifecycle management.
        if credential.status != InstagramCredentialStatus.ACTIVE:
            return {
                "status": "skipped",
                "credential_id": str(credential_id),
                "credential_status": credential.status,
            }

        now = timezone.now()
        refresh_window = self.get_refresh_window()

        # ----------------------------------------------------
        # RE-CHECK AFTER REDIS LOCK
        # ----------------------------------------------------

        if (
            credential.token_expires_at
            and credential.token_expires_at > now + refresh_window
        ):
            return {
                "status": "not_due",
                "credential_id": str(credential_id),
            }

        # ----------------------------------------------------
        # ALREADY EXPIRED
        #
        # Important:
        # We do NOT blindly refresh an already expired token.
        # Reauthorization/reconnect is required.
        # ----------------------------------------------------

        if credential.token_expires_at and credential.token_expires_at <= now:
            self._mark_expired(credential)

            return {
                "status": "expired",
                "credential_id": str(credential_id),
            }

        # ----------------------------------------------------
        # DECRYPT CURRENT TOKEN
        # ----------------------------------------------------

        try:
            access_token = decrypt_token(
                credential.encrypted_access_token,
            )

        except InstagramIntegrationError:
            logger.exception(
                "Unable to decrypt Instagram token for " "credential %s.",
                credential_id,
            )

            self._mark_error(credential)

            return {
                "status": "error",
                "credential_id": str(credential_id),
                "reason": "token_decryption_failed",
            }

        # ----------------------------------------------------
        # CALL INSTAGRAM REFRESH API
        # ----------------------------------------------------

        try:
            response = self.client.refresh_long_lived_token(
                access_token=access_token,
            )

        except InstagramAPIError as exc:
            return self._handle_refresh_error(
                credential=credential,
                error=exc,
            )

        except Exception:
            # Unexpected application/network error.
            #
            # Do NOT permanently mark the credential ERROR here.
            # The token may still be valid. The next lifecycle
            # cycle should be allowed to retry.
            logger.exception(
                "Unexpected Instagram token refresh error " "for credential %s.",
                credential_id,
            )

            return {
                "status": "retry",
                "credential_id": str(credential_id),
                "reason": "unexpected_error",
            }

        # ----------------------------------------------------
        # VALIDATE PROVIDER RESPONSE
        # ----------------------------------------------------

        new_access_token = response.get("access_token")
        expires_in = response.get("expires_in")

        if not new_access_token:
            logger.error(
                "Instagram refresh response did not contain "
                "access_token for credential %s.",
                credential_id,
            )

            # Do not destroy an otherwise potentially valid
            # credential because of a malformed response.
            return {
                "status": "retry",
                "credential_id": str(credential_id),
                "reason": "missing_access_token",
            }

        try:
            expires_in = int(expires_in)
        except (TypeError, ValueError):
            logger.error(
                "Instagram refresh response returned invalid "
                "expires_in for credential %s.",
                credential_id,
            )

            return {
                "status": "retry",
                "credential_id": str(credential_id),
                "reason": "invalid_expires_in",
            }

        if expires_in <= 0:
            logger.error(
                "Instagram refresh response returned non-positive "
                "expires_in for credential %s.",
                credential_id,
            )

            return {
                "status": "retry",
                "credential_id": str(credential_id),
                "reason": "invalid_expiry",
            }

        # ----------------------------------------------------
        # ENCRYPT NEW TOKEN
        # ----------------------------------------------------

        try:
            encrypted_token = encrypt_token(
                new_access_token,
            )

        except InstagramIntegrationError:
            logger.exception(
                "Unable to encrypt refreshed Instagram token " "for credential %s.",
                credential_id,
            )

            self._mark_error(credential)

            return {
                "status": "error",
                "credential_id": str(credential_id),
                "reason": "token_encryption_failed",
            }

        new_expires_at = timezone.now() + timedelta(seconds=expires_in)

        # ----------------------------------------------------
        # PERSIST NEW TOKEN
        # ----------------------------------------------------

        with transaction.atomic():
            credential = (
                InstagramAccountCredential.objects.select_for_update()
                .select_related("social_account")
                .get(
                    id=credential_id,
                )
            )

            # A disconnect/revoke could have happened while
            # the provider API request was running.
            if credential.status != InstagramCredentialStatus.ACTIVE:
                logger.info(
                    "Instagram credential %s state changed "
                    "during refresh. Current status=%s",
                    credential_id,
                    credential.status,
                )

                return {
                    "status": "state_changed",
                    "credential_id": str(credential_id),
                    "credential_status": credential.status,
                }

            credential.encrypted_access_token = encrypted_token
            credential.token_expires_at = new_expires_at
            credential.status = InstagramCredentialStatus.ACTIVE
            credential.last_verified_at = timezone.now()

            credential.save(
                update_fields=[
                    "encrypted_access_token",
                    "token_expires_at",
                    "status",
                    "last_verified_at",
                    "updated_at",
                ],
            )

            social_account = credential.social_account

            social_account.status = SocialAccountStatus.CONNECTED
            social_account.is_valid = True
            social_account.last_synced_at = timezone.now()

            social_account.save(
                update_fields=[
                    "status",
                    "is_valid",
                    "last_synced_at",
                    "updated_at",
                ],
            )

        logger.info(
            "Instagram token refreshed successfully "
            "for credential %s. New expiry=%s",
            credential_id,
            new_expires_at,
        )

        return {
            "status": "refreshed",
            "credential_id": str(credential_id),
            "expires_at": new_expires_at.isoformat(),
        }

    # ========================================================
    # REFRESH ERROR HANDLING
    # ========================================================

    def _handle_refresh_error(
        self,
        *,
        credential,
        error,
    ):
        """
        Classify Instagram API refresh errors.

        Permanent credential failures:
            -> EXPIRED
            -> user must reconnect

        Temporary provider failures:
            -> keep ACTIVE
            -> next lifecycle cycle can retry

        Other provider errors:
            -> ERROR
            -> requires attention
        """

        status_code = error.status_code

        payload = error.error_payload or {}

        error_data = payload.get("error")

        if not isinstance(error_data, dict):
            error_data = {}

        error_code = error_data.get("code")
        error_subcode = error_data.get("error_subcode")

        message = str(
            error_data.get(
                "message",
                str(error),
            )
        ).lower()

        # ----------------------------------------------------
        # PERMANENT TOKEN FAILURE
        # ----------------------------------------------------

        invalid_token = status_code == 400 and (
            error_code in {100, 190}
            or "invalid access token" in message
            or "expired" in message
            or "revoked" in message
            or "invalid token" in message
        )

        if invalid_token:
            self._mark_expired(credential)

            logger.warning(
                "Instagram credential %s is invalid or "
                "expired. status=%s code=%s subcode=%s",
                credential.id,
                status_code,
                error_code,
                error_subcode,
            )

            return {
                "status": "expired",
                "credential_id": str(credential.id),
                "reason": "provider_token_invalid",
            }

        # ----------------------------------------------------
        # TEMPORARY PROVIDER FAILURE
        # ----------------------------------------------------

        temporary_error = (
            status_code is None
            or status_code == 408
            or status_code == 429
            or 500 <= status_code <= 599
        )

        if temporary_error:
            logger.warning(
                "Temporary Instagram token refresh failure "
                "for credential %s. status=%s code=%s",
                credential.id,
                status_code,
                error_code,
            )

            # IMPORTANT:
            # Keep credential ACTIVE.
            #
            # This allows the next Celery Beat cycle to retry
            # while the token is still within its refresh window.
            return {
                "status": "retry",
                "credential_id": str(credential.id),
                "reason": "temporary_provider_error",
            }

        # ----------------------------------------------------
        # OTHER PROVIDER ERROR
        # ----------------------------------------------------

        self._mark_error(credential)

        logger.error(
            "Instagram token refresh failed permanently for "
            "credential %s. status=%s code=%s subcode=%s",
            credential.id,
            status_code,
            error_code,
            error_subcode,
        )

        return {
            "status": "error",
            "credential_id": str(credential.id),
            "reason": "provider_error",
        }

    # ========================================================
    # MARK EXPIRED
    # ========================================================

    @staticmethod
    def _mark_expired(credential):
        """
        Mark credential and related SocialAccount as expired.

        A manually revoked credential is never changed back into
        another automatic lifecycle state.
        """

        with transaction.atomic():
            credential = (
                InstagramAccountCredential.objects.select_for_update()
                .select_related("social_account")
                .get(id=credential.id)
            )

            if credential.status == InstagramCredentialStatus.REVOKED:
                return

            credential.status = InstagramCredentialStatus.EXPIRED
            credential.last_verified_at = timezone.now()

            credential.save(
                update_fields=[
                    "status",
                    "last_verified_at",
                    "updated_at",
                ],
            )

            social_account = credential.social_account

            social_account.status = SocialAccountStatus.EXPIRED
            social_account.is_valid = False

            social_account.save(
                update_fields=[
                    "status",
                    "is_valid",
                    "updated_at",
                ],
            )

    # ========================================================
    # MARK ERROR
    # ========================================================

    @staticmethod
    def _mark_error(credential):
        """
        Mark credential as ERROR for permanent application/
        configuration problems.

        This is intentionally NOT used for temporary provider
        outages.
        """

        with transaction.atomic():
            credential = (
                InstagramAccountCredential.objects.select_for_update()
                .select_related("social_account")
                .get(id=credential.id)
            )

            if credential.status == InstagramCredentialStatus.REVOKED:
                return

            credential.status = InstagramCredentialStatus.ERROR
            credential.last_verified_at = timezone.now()

            credential.save(
                update_fields=[
                    "status",
                    "last_verified_at",
                    "updated_at",
                ],
            )

            social_account = credential.social_account

            social_account.status = SocialAccountStatus.ERROR
            social_account.is_valid = False

            social_account.save(
                update_fields=[
                    "status",
                    "is_valid",
                    "updated_at",
                ],
            )

    # ========================================================
    # REFRESH ALL DUE CREDENTIALS
    # ========================================================

    def refresh_due_credentials(self):
        """
        Find ACTIVE Instagram credentials that are due for
        refresh and process them independently.

        One account failure must not prevent other accounts
        from being processed.
        """

        credentials = (
            InstagramAccountCredential.objects.filter(
                is_deleted=False,
                status=InstagramCredentialStatus.ACTIVE,
            )
            .only(
                "id",
                "status",
                "token_expires_at",
            )
            .order_by("token_expires_at")
        )

        result = {
            "checked": 0,
            "refreshed": 0,
            "expired": 0,
            "errors": 0,
            "skipped": 0,
            "locked": 0,
            "retry": 0,
        }

        now = timezone.now()

        for credential in credentials.iterator():
            result["checked"] += 1

            if not self.credential_needs_refresh(
                credential,
                now=now,
            ):
                result["skipped"] += 1
                continue

            try:
                outcome = self.refresh_credential(
                    credential.id,
                )
            except Exception:
                # One unexpected credential must not stop the
                # entire organization's/account processing.
                logger.exception(
                    "Unexpected lifecycle failure for " "Instagram credential %s.",
                    credential.id,
                )

                result["errors"] += 1
                continue

            status = outcome.get("status")

            if status == "refreshed":
                result["refreshed"] += 1

            elif status == "expired":
                result["expired"] += 1

            elif status == "error":
                result["errors"] += 1

            elif status == "retry":
                result["retry"] += 1

            elif status == "locked":
                result["locked"] += 1

            else:
                result["skipped"] += 1

        return result
