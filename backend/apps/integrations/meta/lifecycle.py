import logging
import re
from datetime import datetime, timezone as datetime_timezone
from typing import Dict, Optional

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.social_accounts.models import (
    SocialAccount,
    SocialAccountStatus,
)

from .client import MetaAPIClient
from .crypto import decrypt_token, encrypt_token
from .exceptions import MetaAPIError
from .models import (
    MetaAccountCredential,
    MetaCredentialStatus,
    MetaCredentialType,
    MetaTokenMaintenanceRun,
)
from .selectors import get_meta_connection_credential

logger = logging.getLogger(__name__)

_RELEASE_LOCK_SCRIPT = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""


class MetaTokenLifecycleService:
    """
    Production-grade lifecycle management for Facebook Page
    access tokens.

    Facebook Page tokens are handled differently from Instagram
    long-lived user tokens.

    Lifecycle strategy:

        1. Validate the currently stored Page token.
        2. If valid:
               keep ACTIVE
               update last_verified_at
               mark SocialAccount connected/valid
        3. If invalid:
               use the parent Meta USER token
               request a fresh Page token
        4. Validate the newly received Page token.
        5. Save the new token atomically.
        6. If recovery fails because authorization is lost:
               mark Page credential INVALID
               mark SocialAccount ERROR
        7. Temporary provider/network errors:
               do not invalidate the account
               retry on the next scheduled cycle.
        8. Manually REVOKED credentials are never restored
           automatically.
    """

    LOCK_TIMEOUT_SECONDS = getattr(
        settings,
        "META_TOKEN_LIFECYCLE_LOCK_TIMEOUT_SECONDS",
        5 * 60,
    )

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
        *,
        api_client: Optional[MetaAPIClient] = None,
    ):
        self.api = api_client or MetaAPIClient()

    @staticmethod
    def _safe_parent_permissions(response, *, sensitive_values=()):
        """Keep only permission names and normalized provider statuses."""
        if not isinstance(response, dict) or not isinstance(response.get("data"), list):
            return None
        safe = []
        for item in response["data"]:
            if not isinstance(item, dict):
                continue
            name = item.get("permission")
            if not isinstance(name, str) or not re.fullmatch(
                r"[a-z][a-z0-9_]{0,99}",
                name,
            ):
                continue
            if name in sensitive_values:
                continue
            status = item.get("status")
            if (
                not isinstance(status, str)
                or status.lower() not in {"granted", "declined", "expired"}
            ):
                status = "unknown"
            safe.append({"permission": name, "status": status.lower()})
        return safe

    @staticmethod
    def _provider_datetime(value):
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            return datetime.fromtimestamp(value, tz=datetime_timezone.utc)
        return None

    @staticmethod
    def _parent_error_is_definitive(error):
        details = MetaAPIClient.safe_error_metadata(error)
        return (
            details["http_status"] in {401, 403}
            or details["graph_error_code"] in {10, 190, 200}
        )

    @staticmethod
    def _save_parent_health_if_current(
        credential,
        *,
        expected_access_token,
        expected_updated_at,
        expected_last_verified_at,
        **updates,
    ):
        """Save health data only if this is still the credential checked."""
        with transaction.atomic():
            current = (
                MetaAccountCredential.objects.select_for_update()
                .filter(
                    pk=credential.pk,
                    credential_type=MetaCredentialType.USER,
                    is_deleted=False,
                )
                .first()
            )
            if (
                current is None
                or current.access_token != expected_access_token
                or current.updated_at != expected_updated_at
                or current.last_verified_at != expected_last_verified_at
            ):
                return None

            for field, value in updates.items():
                setattr(current, field, value)
            current.save(update_fields=[*updates, "updated_at"])
            return current.updated_at

    def _check_parent_user_credential(self, credential):
        """Health-check one USER credential without changing its token/expiry."""
        expected_access_token = credential.access_token
        expected_updated_at = credential.updated_at
        expected_last_verified_at = credential.last_verified_at
        health_updated_at = expected_updated_at
        try:
            user_token = decrypt_token(expected_access_token)
            if not user_token:
                raise MetaAPIError("Meta USER credential is empty.")
            debug = self.api.diagnose_token(access_token=user_token)
            if not isinstance(debug, dict) or not isinstance(debug.get("is_valid"), bool):
                logger.warning(
                    "Meta parent credential diagnostic was incomplete. credential_id=%s",
                    credential.id,
                )
                return "retry"

            token_type = debug.get("type")
            allowed_types = {"USER", "PAGE", "APP", "CLIENT_APP", "SYSTEM_USER"}
            token_type = (
                token_type.upper()
                if isinstance(token_type, str) and token_type.upper() in allowed_types
                else "unknown"
            )
            expires_at = self._provider_datetime(debug.get("expires_at"))
            data_expires_at = self._provider_datetime(debug.get("data_access_expires_at"))
            checked_at = timezone.now()

            if not debug["is_valid"]:
                health_updated_at = self._save_parent_health_if_current(
                    credential,
                    expected_access_token=expected_access_token,
                    expected_updated_at=expected_updated_at,
                    expected_last_verified_at=expected_last_verified_at,
                    provider_token_type=token_type,
                    provider_is_valid=debug["is_valid"],
                    provider_expires_at=expires_at,
                    data_access_expires_at=data_expires_at,
                    last_health_check_at=checked_at,
                    status=MetaCredentialStatus.INVALID,
                )
                if health_updated_at is None:
                    return "retry"
                logger.warning(
                    "Meta parent token is invalid and requires reconnect. credential_id=%s",
                    credential.id,
                )
                return "reconnect_needed"

            health_updated_at = self._save_parent_health_if_current(
                credential,
                expected_access_token=expected_access_token,
                expected_updated_at=expected_updated_at,
                expected_last_verified_at=expected_last_verified_at,
                provider_token_type=token_type,
                provider_is_valid=debug["is_valid"],
                provider_expires_at=expires_at,
                data_access_expires_at=data_expires_at,
            )
            if health_updated_at is None:
                return "retry"

            permissions_response = self.api.get_user_permissions(access_token=user_token)
            permissions = self._safe_parent_permissions(
                permissions_response,
                sensitive_values={
                    user_token,
                    getattr(settings, "META_APP_SECRET", ""),
                },
            )
            if permissions is None:
                logger.warning(
                    "Meta parent permissions diagnostic was incomplete. credential_id=%s",
                    credential.id,
                )
                return "retry"

            prior_grants = {
                entry.get("permission")
                for entry in credential.granted_permissions
                if isinstance(entry, dict) and entry.get("status") == "granted"
            }
            current_grants = {
                entry["permission"]
                for entry in permissions
                if entry["status"] == "granted"
            }
            required_permission_missing = "pages_show_list" not in current_grants
            permission_lost = (
                "pages_show_list" in prior_grants
                and "pages_show_list" not in current_grants
            )
            expired = bool(
                (expires_at and expires_at <= checked_at)
                or (data_expires_at and data_expires_at <= checked_at)
            )
            if token_type not in {"USER", "SYSTEM_USER"}:
                health_status = MetaCredentialStatus.ERROR
                outcome = "reconnect_needed"
            elif expired:
                health_status = MetaCredentialStatus.EXPIRED
                outcome = "reconnect_needed"
            elif required_permission_missing or permission_lost:
                health_status = MetaCredentialStatus.ERROR
                outcome = "reconnect_needed"
            else:
                health_status = MetaCredentialStatus.ACTIVE
                outcome = "valid"

            health_updated_at = self._save_parent_health_if_current(
                credential,
                expected_access_token=expected_access_token,
                expected_updated_at=health_updated_at,
                expected_last_verified_at=expected_last_verified_at,
                granted_permissions=permissions,
                last_health_check_at=checked_at,
                status=health_status,
            )
            if health_updated_at is None:
                return "retry"
            logger.info(
                "Meta parent credential health checked. credential_id=%s outcome=%s token_type=%s permission_count=%s",
                credential.id,
                outcome,
                token_type,
                len(permissions),
            )
            return outcome
        except MetaAPIError as exc:
            details = self.api.safe_error_metadata(exc)
            if self._is_temporary_error(exc) or not self._parent_error_is_definitive(exc):
                logger.warning(
                    "Meta parent credential health check will retry. credential_id=%s http_status=%s graph_error_code=%s graph_error_subcode=%s",
                    credential.id,
                    details["http_status"],
                    details["graph_error_code"],
                    details["graph_error_subcode"],
                )
                return "retry"
            health_status = (
                MetaCredentialStatus.INVALID
                if details["graph_error_code"] == 190
                else MetaCredentialStatus.ERROR
            )
            health_updated_at = self._save_parent_health_if_current(
                credential,
                expected_access_token=expected_access_token,
                expected_updated_at=health_updated_at,
                expected_last_verified_at=expected_last_verified_at,
                status=health_status,
            )
            if health_updated_at is None:
                return "retry"
            logger.warning(
                "Meta parent credential requires reconnect. credential_id=%s http_status=%s graph_error_code=%s graph_error_subcode=%s",
                credential.id,
                details["http_status"],
                details["graph_error_code"],
                details["graph_error_subcode"],
            )
            return "reconnect_needed"
        except Exception:
            logger.warning(
                "Meta parent credential health check failed safely. credential_id=%s",
                credential.id,
            )
            return "retry"

    def _mark_parent_reconnect_needed(self, page_credential, error):
        parent = self._get_parent_user_credential(page_credential=page_credential)
        if parent is None:
            return
        details = self.api.safe_error_metadata(error)
        parent.status = (
            MetaCredentialStatus.INVALID
            if details["graph_error_code"] == 190
            else MetaCredentialStatus.ERROR
        )
        parent.save(update_fields=["status", "updated_at"])

    # ========================================================
    # REDIS DISTRIBUTED LOCK
    # ========================================================

    def _acquire_lock(
        self,
        credential_id: str,
    ) -> Optional[str]:
        """
        Prevent multiple Celery workers from processing the
        same Meta Page credential at the same time.
        """

        lock_key = f"meta:page-token-lifecycle:{credential_id}"

        lock_token = f"{credential_id}:" f"{timezone.now().timestamp()}"

        acquired = cache.add(
            lock_key,
            lock_token,
            timeout=self.LOCK_TIMEOUT_SECONDS,
        )

        if not acquired:
            return None

        return lock_token

    def _release_lock(
        self,
        credential_id: str,
        lock_token: str,
    ) -> None:
        """
        Release the Redis lock only when it still belongs
        to this lifecycle execution.
        """

        lock_key = f"meta:page-token-lifecycle:{credential_id}"

        try:
            redis_client = cache._cache.get_client(write=True)
            serialized_lock_token = cache._cache._serializer.dumps(lock_token)
            redis_client.eval(
                _RELEASE_LOCK_SCRIPT,
                1,
                cache.make_key(lock_key),
                serialized_lock_token,
            )

        except Exception:
            logger.error(
                "Failed to release Meta lifecycle lock. " "credential_id=%s",
                credential_id,
            )

    # ========================================================
    # ERROR CLASSIFICATION
    # ========================================================

    @staticmethod
    def _is_temporary_error(
        exc: MetaAPIError,
    ) -> bool:
        """
        Temporary errors must not cause a reconnect.

        Examples:
            429
            5xx
            timeout/network errors
            connection errors
        """

        status_code = getattr(
            exc,
            "status_code",
            None,
        )

        if status_code is None:
            return True

        if status_code == 429:
            return True

        if 500 <= status_code <= 599:
            return True

        return False

    @staticmethod
    def _is_authentication_error(
        exc: MetaAPIError,
    ) -> bool:
        """
        Detect errors that indicate the access token or
        authorization is no longer usable.
        """

        status_code = getattr(
            exc,
            "status_code",
            None,
        )

        if status_code in {
            400,
            401,
            403,
        }:
            return True

        message = str(exc).lower()

        authentication_keywords = (
            "invalid oauth",
            "access token",
            "expired",
            "oauth",
            "permission",
            "permissions",
            "authorization",
            "unauthorized",
            "not authorized",
            "session",
            "revoked",
        )

        return any(keyword in message for keyword in authentication_keywords)

    # ========================================================
    # VALIDATE PAGE TOKEN
    # ========================================================

    def _validate_page_token(
        self,
        *,
        page_id: str,
        page_access_token: str,
    ) -> dict:
        """
        Validate the currently stored Facebook Page token.

        We intentionally perform a real Page Graph API request
        instead of relying only on token expiry metadata.

        Successful response means the Page token is currently
        usable for that Page.
        """

        if not page_id:
            raise MetaAPIError(
                "Facebook Page ID is required.",
            )

        if not page_access_token:
            raise MetaAPIError(
                "Facebook Page access token is required.",
            )

        response = self.api.get(
            f"/{page_id}",
            access_token=page_access_token,
            params={
                "fields": "id,name",
            },
        )

        returned_page_id = str(
            response.get("id") or "",
        )

        if returned_page_id and returned_page_id != str(page_id):
            raise MetaAPIError(
                "Meta returned a different Facebook Page ID.",
                error_payload=response,
            )

        return response

    # ========================================================
    # GET PARENT META USER CREDENTIAL
    # ========================================================

    def _get_parent_user_credential(
        self,
        *,
        page_credential: MetaAccountCredential,
    ) -> Optional[MetaAccountCredential]:
        """
        PAGE credential intentionally does not have a direct
        social_connection.

        The parent connection is:

            Page Credential
                  ↓
            SocialAccount
                  ↓
            SocialAccount.connection
                  ↓
            SocialConnection
                  ↓
            USER Credential
        """

        social_account = page_credential.social_account

        if social_account is None:
            return None

        connection = social_account.connection

        if connection is None:
            return None

        try:
            # return get_meta_connection_credential(
            #     connection,
            # )
            return get_meta_connection_credential(
                social_connection=page_credential.social_account.connection,
            )

        except Exception:
            logger.error(
                "Unable to resolve parent Meta USER credential. "
                "page_credential_id=%s",
                page_credential.id,
            )

            return None

    # ========================================================
    # REISSUE PAGE TOKEN
    # ========================================================

    def _reissue_page_token(
        self,
        *,
        page_credential: MetaAccountCredential,
    ) -> str:
        """
        Request a fresh Facebook Page access token using
        the parent Meta USER access token.
        """

        social_account = page_credential.social_account

        if social_account is None:
            raise MetaAPIError(
                "Page credential is not linked to a SocialAccount.",
            )

        page_id = str(
            social_account.platform_account_id or "",
        ).strip()

        if not page_id:
            raise MetaAPIError(
                "Facebook Page ID is missing.",
            )

        user_credential = self._get_parent_user_credential(
            page_credential=page_credential,
        )

        if user_credential is None:
            raise MetaAPIError(
                "Parent Meta USER credential was not found.",
            )

        if user_credential.status != MetaCredentialStatus.ACTIVE:
            raise MetaAPIError(
                "Parent Meta USER credential is not active.",
            )

        if not user_credential.access_token:
            raise MetaAPIError(
                "Parent Meta USER credential has no access token.",
            )

        try:
            user_access_token = decrypt_token(
                user_credential.access_token,
            )

        except Exception as exc:
            logger.error(
                "Failed to decrypt Meta USER access token. " "credential_id=%s",
                user_credential.id,
            )

            raise MetaAPIError(
                "Unable to decrypt Meta USER access token.",
            ) from exc

        if not user_access_token:
            raise MetaAPIError(
                "Meta USER access token is empty.",
            )

        page_data = self.api.get_page(
            page_id=page_id,
            access_token=user_access_token,
        )

        new_page_token = page_data.get(
            "access_token",
        )

        if not new_page_token:
            raise MetaAPIError(
                "Meta did not return a new Facebook Page " "access token.",
                error_payload=page_data,
            )

        return str(new_page_token)

    # ========================================================
    # MARK SOCIAL ACCOUNT CONNECTED
    # ========================================================

    @staticmethod
    def _mark_account_connected(
        social_account: SocialAccount,
    ) -> None:
        """
        Restore the SocialAccount to a healthy state.
        """

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

    # ========================================================
    # MARK SOCIAL ACCOUNT ERROR
    # ========================================================

    @staticmethod
    def _mark_account_error(
        social_account: SocialAccount,
    ) -> None:
        """
        Keep the SocialAccount record but mark it unhealthy.

        Frontend can use this state to show Reconnect.
        """

        social_account.status = SocialAccountStatus.ERROR

        social_account.is_valid = False
        social_account.last_synced_at = timezone.now()

        social_account.save(
            update_fields=[
                "status",
                "is_valid",
                "last_synced_at",
                "updated_at",
            ],
        )

    # ========================================================
    # SAVE VERIFIED PAGE TOKEN
    # ========================================================

    @transaction.atomic
    def _save_verified_page_token(
        self,
        *,
        credential_id: str,
        page_access_token: str,
    ) -> None:
        """
        Save a successfully verified/reissued Page token.

        Facebook Page token expiry is intentionally not inferred
        here. Current architecture stores token_expires_at=None
        for Page credentials.
        """

        # IMPORTANT:
        # Do not use select_related() together with select_for_update()
        # here because social_account is nullable.
        credential = MetaAccountCredential.objects.select_for_update().get(
            id=credential_id,
        )

        if credential.status == MetaCredentialStatus.REVOKED:
            return

        credential.access_token = encrypt_token(
            page_access_token,
        )

        credential.token_expires_at = None

        credential.status = MetaCredentialStatus.ACTIVE

        credential.last_verified_at = timezone.now()

        credential.save(
            update_fields=[
                "access_token",
                "token_expires_at",
                "status",
                "last_verified_at",
                "updated_at",
            ],
        )

        if credential.social_account:
            self._mark_account_connected(
                credential.social_account,
            )

    # ========================================================
    # MARK PAGE INVALID
    # ========================================================

    @transaction.atomic
    def _mark_page_invalid(
        self,
        *,
        credential_id: str,
    ) -> None:
        """
        Mark a Page credential invalid after recovery fails.

        Manual REVOKED state is never overwritten.
        """

        # IMPORTANT:
        # Lock only MetaAccountCredential.
        credential = MetaAccountCredential.objects.select_for_update().get(
            id=credential_id,
        )

        if credential.status == MetaCredentialStatus.REVOKED:
            return

        credential.status = MetaCredentialStatus.INVALID

        credential.last_verified_at = timezone.now()

        credential.save(
            update_fields=[
                "status",
                "last_verified_at",
                "updated_at",
            ],
        )

        if credential.social_account:
            self._mark_account_error(
                credential.social_account,
            )

    # ========================================================
    # PROCESS SINGLE PAGE CREDENTIAL
    # ========================================================

    def process_page_credential(
        self,
        credential: MetaAccountCredential,
    ) -> str:
        """
        Process one Facebook Page credential.

        Possible results:

            verified
            refreshed
            invalid
            retry
            revoked
            locked
            skipped
        """

        if credential.credential_type != MetaCredentialType.PAGE:
            return "skipped"

        if credential.status == MetaCredentialStatus.REVOKED:
            return "revoked"

        social_account = credential.social_account

        if social_account is None:
            return "skipped"

        if social_account.platform != "facebook":
            return "skipped"

        if social_account.is_deleted:
            return "skipped"

        page_id = str(
            social_account.platform_account_id or "",
        ).strip()

        if not page_id:
            return "skipped"

        lock_token = self._acquire_lock(
            str(credential.id),
        )

        if lock_token is None:
            return "locked"

        try:
            # Re-read after acquiring lock.
            #
            # IMPORTANT:
            # No select_related() here because this object may
            # later participate in select_for_update() operations
            # and both relationships are nullable.
            credential = MetaAccountCredential.objects.get(
                id=credential.id,
            )

            if credential.status == MetaCredentialStatus.REVOKED:
                return "revoked"

            if not credential.access_token:
                self._mark_page_invalid(
                    credential_id=str(
                        credential.id,
                    ),
                )

                return "invalid"

            # ------------------------------------------------
            # STEP 1
            # Validate existing Page token
            # ------------------------------------------------

            try:
                current_page_token = decrypt_token(
                    credential.access_token,
                )

            except Exception:
                logger.error(
                    "Failed to decrypt Facebook Page token. " "credential_id=%s",
                    credential.id,
                )

                self._mark_page_invalid(
                    credential_id=str(
                        credential.id,
                    ),
                )

                return "invalid"

            try:
                self._validate_page_token(
                    page_id=page_id,
                    page_access_token=current_page_token,
                )

                with transaction.atomic():

                    # IMPORTANT:
                    # Lock ONLY MetaAccountCredential.
                    locked_credential = (
                        MetaAccountCredential.objects.select_for_update().get(
                            id=credential.id,
                        )
                    )

                    if locked_credential.status == MetaCredentialStatus.REVOKED:
                        return "revoked"

                    locked_credential.status = MetaCredentialStatus.ACTIVE

                    locked_credential.last_verified_at = timezone.now()

                    locked_credential.save(
                        update_fields=[
                            "status",
                            "last_verified_at",
                            "updated_at",
                        ],
                    )

                    if locked_credential.social_account:
                        self._mark_account_connected(
                            locked_credential.social_account,
                        )

                return "verified"

            except MetaAPIError as exc:

                # Temporary Meta/network issue.
                if self._is_temporary_error(exc):
                    error_details = self.api.safe_error_metadata(exc)
                    logger.warning(
                        "Temporary Meta error while validating "
                        "Facebook Page token. "
                        "credential_id=%s http_status=%s "
                        "graph_error_code=%s graph_error_subcode=%s",
                        credential.id,
                        error_details["http_status"],
                        error_details["graph_error_code"],
                        error_details["graph_error_subcode"],
                    )

                    return "retry"

                # Unexpected non-authentication error.
                if not self._is_authentication_error(exc):
                    error_details = self.api.safe_error_metadata(exc)
                    logger.error(
                        "Unexpected Meta error while validating "
                        "Facebook Page token. "
                        "credential_id=%s http_status=%s "
                        "graph_error_code=%s graph_error_subcode=%s",
                        credential.id,
                        error_details["http_status"],
                        error_details["graph_error_code"],
                        error_details["graph_error_subcode"],
                    )

                    return "retry"

                # Authentication failure means we proceed
                # to Page token recovery.
                logger.warning(
                    "Facebook Page token appears invalid. "
                    "Attempting recovery. credential_id=%s",
                    credential.id,
                )

            # ------------------------------------------------
            # STEP 2
            # Recover Page token using USER token
            # ------------------------------------------------

            parent_credential = self._get_parent_user_credential(
                page_credential=credential,
            )
            if (
                parent_credential is None
                or parent_credential.status != MetaCredentialStatus.ACTIVE
            ):
                logger.warning(
                    "Facebook Page recovery deferred because parent Meta credential needs reconnect. credential_id=%s",
                    credential.id,
                )
                return "reconnect_needed"

            try:
                new_page_token = self._reissue_page_token(
                    page_credential=credential,
                )
            except MetaAPIError as exc:
                if self._is_temporary_error(exc):
                    details = self.api.safe_error_metadata(exc)
                    logger.warning(
                    "Temporary Meta error while recovering Facebook Page token. "
                    "credential_id=%s http_status=%s graph_error_code=%s "
                    "graph_error_subcode=%s",
                    credential.id,
                    details["http_status"],
                    details["graph_error_code"],
                    details["graph_error_subcode"],
                    )
                    return "retry"
                if self._parent_error_is_definitive(exc):
                    self._mark_parent_reconnect_needed(credential, exc)
                    details = self.api.safe_error_metadata(exc)
                    logger.warning(
                    "Parent Meta credential requires reconnect after Page recovery failure. "
                    "credential_id=%s http_status=%s graph_error_code=%s "
                    "graph_error_subcode=%s",
                    credential.id,
                    details["http_status"],
                    details["graph_error_code"],
                    details["graph_error_subcode"],
                    )
                    return "reconnect_needed"
                return "retry"

            try:
                # ------------------------------------------------
                # STEP 3
                # Validate newly issued token
                # ------------------------------------------------

                self._validate_page_token(
                    page_id=page_id,
                    page_access_token=new_page_token,
                )

                # ------------------------------------------------
                # STEP 4
                # Atomically save new token
                # ------------------------------------------------

                self._save_verified_page_token(
                    credential_id=str(
                        credential.id,
                    ),
                    page_access_token=new_page_token,
                )

                logger.info(
                    "Facebook Page token successfully recovered. "
                    "credential_id=%s page_id=%s",
                    credential.id,
                    page_id,
                )

                return "refreshed"

            except MetaAPIError as exc:

                if self._is_temporary_error(exc):
                    error_details = self.api.safe_error_metadata(exc)
                    logger.warning(
                        "Temporary Meta error while recovering "
                        "Facebook Page token. "
                        "credential_id=%s http_status=%s "
                        "graph_error_code=%s graph_error_subcode=%s",
                        credential.id,
                        error_details["http_status"],
                        error_details["graph_error_code"],
                        error_details["graph_error_subcode"],
                    )

                    return "retry"

                if self._is_authentication_error(exc):
                    error_details = self.api.safe_error_metadata(exc)
                    logger.warning(
                        "Facebook Page token recovery failed. "
                        "Reconnect required. "
                        "credential_id=%s http_status=%s "
                        "graph_error_code=%s graph_error_subcode=%s",
                        credential.id,
                        error_details["http_status"],
                        error_details["graph_error_code"],
                        error_details["graph_error_subcode"],
                    )

                    self._mark_page_invalid(
                        credential_id=str(
                            credential.id,
                        ),
                    )

                    return "invalid"

                error_details = self.api.safe_error_metadata(exc)
                logger.error(
                    "Unexpected Meta error during Page token "
                    "recovery. credential_id=%s http_status=%s "
                    "graph_error_code=%s graph_error_subcode=%s",
                    credential.id,
                    error_details["http_status"],
                    error_details["graph_error_code"],
                    error_details["graph_error_subcode"],
                )

                return "retry"

            except Exception:
                logger.error(
                    "Unexpected exception during Facebook "
                    "Page token lifecycle. credential_id=%s",
                    credential.id,
                )

                return "retry"

        finally:
            self._release_lock(
                str(credential.id),
                lock_token,
            )

    # ========================================================
    # PROCESS ALL ACTIVE FACEBOOK PAGE CREDENTIALS
    # ========================================================

    def refresh_due_credentials(self) -> Dict[str, int]:
        """
        Process all active Facebook Page credentials.

        Unlike Instagram, this does not use a 7-day expiry
        window.

        Every scheduled execution validates active Page tokens.
        Invalid tokens are recovered through their parent
        Meta USER credential when possible.
        """

        result = {
            "checked": 0,
            "verified": 0,
            "refreshed": 0,
            "valid": 0,
            "invalid": 0,
            "revoked": 0,
            "retry": 0,
            "reconnect_needed": 0,
            "parent_checked": 0,
            "parent_valid": 0,
            "parent_invalid": 0,
            "parent_retry": 0,
            "skipped": 0,
            "locked": 0,
        }

        credentials = (
            MetaAccountCredential.objects.select_related(
                "social_account",
                "social_account__connection",
            )
            .filter(
                credential_type=MetaCredentialType.PAGE,
                status=MetaCredentialStatus.ACTIVE,
                social_account__isnull=False,
                social_account__is_deleted=False,
                social_account__platform="facebook",
            )
            .order_by("id")
        )

        # Resolve each selected parent USER credential once, then run a single
        # health probe per credential for this maintenance cycle.
        parents = {}
        for page_credential in credentials:
            parent = self._get_parent_user_credential(page_credential=page_credential)
            if parent:
                parents.setdefault(str(parent.id), parent)
        reconnect_parent_ids = set()
        for parent_id, parent in parents.items():
            if parent.status != MetaCredentialStatus.ACTIVE:
                if parent.status in {
                    MetaCredentialStatus.EXPIRED,
                    MetaCredentialStatus.REVOKED,
                    MetaCredentialStatus.INVALID,
                    MetaCredentialStatus.ERROR,
                }:
                    result["parent_invalid"] += 1
                    result["invalid"] += 1
                    reconnect_parent_ids.add(parent_id)
                continue
            result["parent_checked"] += 1
            result["checked"] += 1
            parent_outcome = self._check_parent_user_credential(parent)
            if parent_outcome == "valid":
                result["parent_valid"] += 1
                result["valid"] += 1
            elif parent_outcome == "reconnect_needed":
                result["parent_invalid"] += 1
                result["invalid"] += 1
                reconnect_parent_ids.add(parent_id)
            else:
                result["parent_retry"] += 1
                result["retry"] += 1

        for credential in credentials:
            result["checked"] += 1

            try:
                outcome = self.process_page_credential(
                    credential,
                )

            except Exception:
                logger.error("Unhandled Meta lifecycle error. credential_id=%s", credential.id)

                result["retry"] += 1
                continue

            if outcome in {
                "verified",
                "refreshed",
                "invalid",
                "revoked",
                "retry",
                "skipped",
                "locked",
            }:
                result[outcome] += 1

            if outcome in {"verified", "refreshed"}:
                result["valid"] += 1
            elif outcome == "reconnect_needed":
                parent = self._get_parent_user_credential(page_credential=credential)
                if parent:
                    reconnect_parent_ids.add(str(parent.id))
                else:
                    connection_id = getattr(credential.social_account, "connection_id", None)
                    reconnect_parent_ids.add(f"missing-parent:{connection_id or credential.id}")

        # Parent failures make this run partial even when the Page-token probe
        # itself did not need recovery.
        result["reconnect_needed"] = len(reconnect_parent_ids)

        logger.info(
            "Meta Facebook Page token lifecycle completed: %s",
            result,
        )

        return result
