import logging
import time
import uuid

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .lifecycle import MetaTokenLifecycleService
from .models import MetaTokenMaintenanceRun

logger = logging.getLogger(__name__)


class MetaTokenMaintenanceRunPersistenceError(Exception):
    """The task could not safely create or finalize its run record."""


def _user_renewal_run_counters(user_renewal):
    """Map safe USER renewal aggregates onto durable run fields."""
    return {
        "user_renewed": user_renewal["renewed"],
        "user_skipped": user_renewal["skipped"],
        "user_locked": user_renewal["locked"],
        "user_stale": user_renewal["stale"],
        "user_retry": user_renewal["retry"],
    }


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    dont_autoretry_for=(MetaTokenMaintenanceRunPersistenceError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def maintain_meta_tokens_task(self):
    """
    Periodic Facebook Page token lifecycle maintenance.

    The actual lifecycle logic lives inside
    MetaTokenLifecycleService.

    Celery is responsible only for scheduling/executing
    the lifecycle service.
    """

    run_id = uuid.uuid4()
    started_at = timezone.now()
    started_clock = time.monotonic()
    try:
        run = MetaTokenMaintenanceRun.objects.create(
            run_id=run_id,
            started_at=started_at,
            outcome=MetaTokenMaintenanceRun.Outcome.RUNNING,
        )
    except Exception as exc:
        logger.error(
            "Meta token maintenance run record creation failed "
            "run_id=%s error_type=%s outcome=FAILED",
            run_id,
            type(exc).__name__,
        )
        raise MetaTokenMaintenanceRunPersistenceError(
            "Meta token maintenance run record could not be created."
        ) from None
    logger.info(
        "Meta token maintenance started run_id=%s started_at=%s",
        run_id,
        started_at.isoformat(),
    )

    try:
        lifecycle = MetaTokenLifecycleService()
        user_renewal_enabled = bool(
            getattr(settings, "META_USER_TOKEN_AUTO_RENEWAL_ENABLED", False)
        )
        user_renewal = {
            "renewed": 0,
            "skipped": 0,
            "locked": 0,
            "stale": 0,
            "retry": 0,
        }
        if user_renewal_enabled:
            try:
                raw_user_renewal = lifecycle.renew_due_user_credentials()
                if not isinstance(raw_user_renewal, dict):
                    raise TypeError("Invalid USER renewal result.")
                for field in user_renewal:
                    value = raw_user_renewal.get(field, 0)
                    if (
                        not isinstance(value, int)
                        or isinstance(value, bool)
                        or value < 0
                    ):
                        raise TypeError("Invalid USER renewal counter.")
                    user_renewal[field] = value
            except Exception as exc:
                # Keep USER renewal isolated from the existing PAGE maintenance
                # pass, and never log provider exception details.
                user_renewal["retry"] = 1
                logger.warning(
                    "Meta USER token renewal phase failed safely. error_type=%s",
                    type(exc).__name__,
                )

        page_result = lifecycle.refresh_due_credentials()
        page_result = dict(page_result)
        result = {
            **page_result,
            "user_renewal_enabled": user_renewal_enabled,
            "user_renewal": user_renewal,
            "retry": int(page_result.get("retry", 0)) + user_renewal["retry"],
        }
        outcome = (
            MetaTokenMaintenanceRun.Outcome.PARTIAL
            if result.get("invalid", 0)
            or result.get("retry", 0)
            or result.get("reconnect_needed", 0)
            or result.get("locked", 0)
            else MetaTokenMaintenanceRun.Outcome.SUCCESS
        )
        finished_at = timezone.now()
        duration_ms = max(0, int((time.monotonic() - started_clock) * 1000))
        counters = {
            "checked": int(result.get("checked", 0)),
            "valid": int(
                result.get(
                    "valid",
                    result.get("verified", 0) + result.get("refreshed", 0),
                )
            ),
            "invalid": int(result.get("invalid", 0)),
            "retry": int(result.get("retry", 0)),
            "reconnect_needed": int(result.get("reconnect_needed", 0)),
            **_user_renewal_run_counters(user_renewal),
        }
        for field, value in counters.items():
            setattr(run, field, value)
        run.finished_at = finished_at
        run.duration_ms = duration_ms
        run.outcome = outcome
        try:
            run.save(update_fields=[*counters, "finished_at", "duration_ms", "outcome"])
        except Exception as exc:
            logger.error(
                "Meta token maintenance run record finalization failed "
                "run_id=%s error_type=%s outcome=FAILED",
                run_id,
                type(exc).__name__,
            )
            raise MetaTokenMaintenanceRunPersistenceError(
                "Meta token maintenance run record could not be finalized."
            ) from None
        logger.info(
            "Meta token maintenance completed run_id=%s started_at=%s "
            "finished_at=%s duration_ms=%s outcome=%s checked=%s valid=%s "
            "invalid=%s retry=%s reconnect_needed=%s "
            "user_renewal_enabled=%s user_renewed=%s user_skipped=%s "
            "user_locked=%s user_stale=%s user_retry=%s",
            run_id,
            started_at.isoformat(),
            finished_at.isoformat(),
            duration_ms,
            outcome,
            counters["checked"],
            counters["valid"],
            counters["invalid"],
            counters["retry"],
            counters["reconnect_needed"],
            user_renewal_enabled,
            user_renewal["renewed"],
            user_renewal["skipped"],
            user_renewal["locked"],
            user_renewal["stale"],
            user_renewal["retry"],
        )
        return {**result, "run_id": str(run_id), "outcome": outcome}
    except MetaTokenMaintenanceRunPersistenceError:
        raise
    except Exception:
        finished_at = timezone.now()
        duration_ms = max(0, int((time.monotonic() - started_clock) * 1000))
        run.finished_at = finished_at
        run.duration_ms = duration_ms
        run.outcome = MetaTokenMaintenanceRun.Outcome.FAILED
        try:
            run.save(update_fields=["finished_at", "duration_ms", "outcome"])
        except Exception as exc:
            logger.error(
                "Meta token maintenance failed run record could not be finalized "
                "run_id=%s error_type=%s outcome=FAILED",
                run_id,
                type(exc).__name__,
            )
            raise MetaTokenMaintenanceRunPersistenceError(
                "Meta token maintenance failure could not be recorded."
            ) from None
        logger.error(
            "Meta token maintenance failed run_id=%s started_at=%s "
            "finished_at=%s duration_ms=%s outcome=FAILED",
            run_id,
            started_at.isoformat(),
            finished_at.isoformat(),
            duration_ms,
        )
        raise RuntimeError("Meta token maintenance run failed.") from None


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def monitor_meta_user_data_access_expiry_task():
    """Monitor stored USER data-access expiries without provider calls."""
    return MetaTokenLifecycleService().monitor_user_data_access_expiry()
