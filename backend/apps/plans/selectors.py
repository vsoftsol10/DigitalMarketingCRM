from .models import Plan


def plan_queryset():
    """
    Base queryset used by plan read operations.

    Soft-deleted plans are excluded.
    Newest plans are returned first.
    """

    return (
        Plan.objects
        .filter(is_deleted=False)
        .order_by("-created_at")
    )


def get_plans(
    *,
    status=None,
    plan_type=None,
    search=None,
    ordering="-created_at",
):
    """
    Return plans with optional filtering.
    """

    queryset = plan_queryset()

    if status:
        queryset = queryset.filter(
            status=status,
        )

    if plan_type:
        queryset = queryset.filter(
            plan_type__iexact=plan_type,
        )

    if search:
        search = search.strip()

        if search:
            queryset = queryset.filter(
                name__icontains=search,
            )

    allowed_ordering = {
        "created_at",
        "-created_at",
        "name",
        "-name",
        "monthly_price",
        "-monthly_price",
        "yearly_price",
        "-yearly_price",
    }

    if ordering not in allowed_ordering:
        ordering = "-created_at"

    return queryset.order_by(ordering)


def get_plan_by_id(
    plan_id,
):
    """
    Return a single non-deleted plan.
    """

    return (
        plan_queryset()
        .filter(
            id=plan_id,
        )
        .first()
    )


def get_plan_by_code(
    code,
):
    """
    Return a plan by its unique code.
    """

    if not code:
        return None

    return (
        plan_queryset()
        .filter(
            code__iexact=code.strip(),
        )
        .first()
    )


def get_plan_by_type(
    plan_type,
):
    """
    Return a plan by its immutable plan type.
    """

    if not plan_type:
        return None

    return (
        plan_queryset()
        .filter(
            plan_type__iexact=plan_type.strip(),
        )
        .first()
    )