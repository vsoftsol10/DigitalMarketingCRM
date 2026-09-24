from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        "event_type",
        "organization",
        "source",
        "actor",
        "occurred_at",
    )
    list_filter = ("event_type", "source", "is_deleted")
    search_fields = (
        "organization__name",
        "organization__organization_id",
        "idempotency_key",
    )
    readonly_fields = ("id", "created_at", "updated_at", "occurred_at")
    ordering = ("-occurred_at", "-id")
