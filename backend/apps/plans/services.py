from django.db import transaction
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from .models import Plan


def generate_unique_plan_code(name):
    """
    Generate a unique internal plan code from the plan name.

    Example:
        Professional
        -> professional

        Professional (existing)
        -> professional-2
    """

    base_code = slugify(name).strip("-")

    if not base_code:
        base_code = "plan"

    code = base_code
    counter = 2

    while Plan.objects.filter(
        code=code,
    ).exists():
        code = f"{base_code}-{counter}"
        counter += 1

    return code


def build_limits_data(limits):
    """
    Convert frontend limits object into normalized
    database fields.
    """

    limits = limits or {}

    return {
        "accounts_limit": int(limits.get("accounts", 0)),
        "posts_limit": int(limits.get("posts", 0)),
        "videos_limit": int(limits.get("videos", 0)),
        "ads_limit": int(limits.get("ads", 0)),
        "dm_automations_limit": int(limits.get("dm_automations", 0)),
    }


@transaction.atomic
def create_plan(
    *,
    validated_data,
    is_custom=False,
):
    """
    Create a new subscription plan.

    Normal plan:
        plan_type comes from the request.

    Custom plan:
        plan_type is always CUSTOM.
        is_custom is always True.
    """

    data = dict(validated_data)

    # ---------------------------------------------------------
    # Extract frontend-composite fields
    # ---------------------------------------------------------

    name = data.pop(
        "name",
    ).strip()

    plan_type = data.pop(
        "plan_type",
        "",
    )

    limits = data.pop(
        "limits",
        {},
    )

    # ---------------------------------------------------------
    # Plan identity
    # ---------------------------------------------------------

    if is_custom:
        plan_type = "CUSTOM"
        custom_flag = True

    else:
        plan_type = plan_type.strip().upper()

        if not plan_type:
            raise ValidationError({"type": "Plan type is required."})

        custom_flag = False

    # ---------------------------------------------------------
    # Validate plan type uniqueness
    # ---------------------------------------------------------

    if not custom_flag:
        if Plan.objects.filter(
            plan_type__iexact=plan_type,
            is_deleted=False,
        ).exists():
            raise ValidationError(
                {"type": ("A plan with this type " "already exists.")}
            )

    # ---------------------------------------------------------
    # Generate unique internal code
    # ---------------------------------------------------------

    code = generate_unique_plan_code(name)

    # ---------------------------------------------------------
    # Normalize limits
    # ---------------------------------------------------------

    limit_data = build_limits_data(limits)

    # ---------------------------------------------------------
    # Create plan
    # ---------------------------------------------------------

    plan = Plan.objects.create(
        name=name,
        code=code,
        plan_type=plan_type,
        is_custom=custom_flag,
        is_system=False,
        **data,
        **limit_data,
    )

    return plan


@transaction.atomic
def update_plan(
    *,
    plan,
    validated_data,
):
    """
    Update an existing plan.

    Plan identity is immutable:

        name
        code
        plan_type
        is_system
        is_custom

    Only editable configuration is updated.
    """

    data = dict(validated_data)

    limits = data.pop(
        "limits",
        None,
    )

    # ---------------------------------------------------------
    # Identity protection
    # ---------------------------------------------------------

    data.pop(
        "name",
        None,
    )

    data.pop(
        "plan_type",
        None,
    )

    data.pop(
        "code",
        None,
    )

    data.pop(
        "is_system",
        None,
    )

    data.pop(
        "is_custom",
        None,
    )

    # ---------------------------------------------------------
    # Organization-independent fields
    # ---------------------------------------------------------

    for field, value in data.items():
        setattr(
            plan,
            field,
            value,
        )

    # ---------------------------------------------------------
    # Limits
    # ---------------------------------------------------------

    if limits is not None:
        limit_data = build_limits_data(limits)

        for field, value in limit_data.items():
            setattr(
                plan,
                field,
                value,
            )

    plan.save()

    return plan


@transaction.atomic
def delete_plan(
    *,
    plan,
):
    """
    Soft-delete a plan.

    System plans cannot be deleted.
    """

    if plan.is_system:
        raise ValidationError({"detail": ("System plans cannot be deleted.")})

    plan.soft_delete()

    return plan
