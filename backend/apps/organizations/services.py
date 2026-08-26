from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.utils import timezone

from .models import (
    BillingCycle,
    Organization,
    OrganizationContact,
    OrganizationSubscription,
    SubscriptionStatus,
)

from apps.plans.models import Plan

from .utils import generate_unique_slug


def generate_organization_id():
    """
    Generate a human-readable organization identifier.

    Example:
        ORG000001
        ORG000002
    """

    last_organization = Organization.objects.order_by("-organization_id").first()

    if not last_organization:
        return "ORG000001"

    try:
        last_number = int(
            last_organization.organization_id.replace(
                "ORG",
                "",
            )
        )
    except (AttributeError, ValueError):
        last_number = Organization.objects.count()

    return f"ORG{last_number + 1:06d}"


def build_location_data(location):
    """
    Convert frontend's single location field into
    backend location fields.

    Example:
        'Chennai, Tamil Nadu'
        -> city='Chennai'
           state='Tamil Nadu'
    """

    if not location:
        return {
            "city": "",
            "state": "",
            "country": "",
        }

    parts = [part.strip() for part in location.split(",") if part.strip()]

    if len(parts) == 1:
        return {
            "city": parts[0],
            "state": "",
            "country": "",
        }

    if len(parts) == 2:
        return {
            "city": parts[0],
            "state": parts[1],
            "country": "",
        }

    return {
        "city": parts[0],
        "state": parts[1],
        "country": parts[2],
    }


@transaction.atomic
def create_organization(
    *,
    validated_data,
    created_by=None,
):
    """
    Create Organization + primary contact + initial subscription
    in a single transaction.

    Subscription rules:
        - Plan is selected from active plans only by the serializer.
        - Billing cycle is monthly or yearly.
        - Start date is controlled by the server.
        - Monthly expiry = start date + 1 month.
        - Yearly expiry = start date + 1 year.
        - New subscriptions always start as ACTIVE.
        - New subscriptions are marked as current.
    """

    data = dict(validated_data)

    # ---------------------------------------------------------
    # Extract frontend-composite fields
    # ---------------------------------------------------------

    contact_name = data.pop(
        "contact_name",
        "",
    )

    contact_email = data.pop(
        "contact_email",
        "",
    )

    contact_phone = data.pop(
        "contact_phone",
        "",
    )

    subscription_plan = data.pop(
        "subscription_plan",
    )

    billing_cycle = data.pop(
        "billing_cycle",
    )

    location = data.pop(
        "location",
        "",
    )

    # ---------------------------------------------------------
    # Server-controlled subscription fields
    # ---------------------------------------------------------

    # Do not accept subscription status/date values
    # from the frontend.
    data.pop(
        "subscription_status",
        None,
    )

    data.pop(
        "subscription_start",
        None,
    )

    data.pop(
        "subscription_expiry",
        None,
    )

    # Social accounts are managed through the
    # dedicated social account flow.
    data.pop(
        "social_accounts",
        None,
    )

    # ---------------------------------------------------------
    # Location mapping
    # ---------------------------------------------------------

    location_data = build_location_data(location)

    data.update(location_data)

    # ---------------------------------------------------------
    # Organization
    # ---------------------------------------------------------

    organization = Organization.objects.create(
        organization_id=generate_organization_id(),
        slug=generate_unique_slug(data["name"]),
        created_by=created_by,
        **data,
    )

    # ---------------------------------------------------------
    # Primary Contact
    # ---------------------------------------------------------

    if contact_name or contact_email:
        OrganizationContact.objects.create(
            organization=organization,
            name=contact_name,
            email=contact_email,
            phone=contact_phone,
            is_primary=True,
        )

    # ---------------------------------------------------------
    # Subscription Dates
    # ---------------------------------------------------------

    subscription_start = timezone.localdate()

    if billing_cycle == BillingCycle.MONTHLY:
        subscription_expiry = subscription_start + relativedelta(months=1)

    elif billing_cycle == BillingCycle.YEARLY:
        subscription_expiry = subscription_start + relativedelta(years=1)

    else:
        # Defensive check.
        # Serializer ChoiceField should normally prevent this.
        raise ValueError("Unsupported billing cycle.")

    # ---------------------------------------------------------
    # Initial Subscription
    # ---------------------------------------------------------

    OrganizationSubscription.objects.create(
        organization=organization,
        plan=subscription_plan,
        billing_cycle=billing_cycle,
        status=SubscriptionStatus.ACTIVE,
        start_date=subscription_start,
        expiry_date=subscription_expiry,
        is_current=True,
    )

    return organization


@transaction.atomic
def update_organization(
    *,
    organization,
    validated_data,
):
    """
    Update Organization + primary contact +
    subscription atomically.

    Subscription start and expiry dates are
    server-controlled and are intentionally
    not editable through organization updates.
    """

    data = dict(validated_data)

    # ---------------------------------------------------------
    # Extract contact fields
    # ---------------------------------------------------------

    contact_fields = {
        "contact_name": data.pop(
            "contact_name",
            None,
        ),
        "contact_email": data.pop(
            "contact_email",
            None,
        ),
        "contact_phone": data.pop(
            "contact_phone",
            None,
        ),
    }

    # ---------------------------------------------------------
    # Extract subscription fields
    # ---------------------------------------------------------

    subscription_fields = {
        "subscription_plan": data.pop(
            "subscription_plan",
            None,
        ),
        "billing_cycle": data.pop(
            "billing_cycle",
            None,
        ),
        "subscription_status": data.pop(
            "subscription_status",
            None,
        ),
    }

    # ---------------------------------------------------------
    # Explicitly ignore server-controlled dates
    # ---------------------------------------------------------

    data.pop(
        "subscription_start",
        None,
    )

    data.pop(
        "subscription_expiry",
        None,
    )

    # ---------------------------------------------------------
    # Location
    # ---------------------------------------------------------

    if "location" in data:
        location = data.pop("location")

        data.update(build_location_data(location))

    # ---------------------------------------------------------
    # Social accounts
    # ---------------------------------------------------------

    data.pop(
        "social_accounts",
        None,
    )

    # ---------------------------------------------------------
    # Organization update
    # ---------------------------------------------------------

    if "name" in data:
        organization.slug = generate_unique_slug(
            data["name"],
            instance=organization,
        )

    for field, value in data.items():
        setattr(
            organization,
            field,
            value,
        )

    organization.save()

    # ---------------------------------------------------------
    # Primary contact
    # ---------------------------------------------------------

    has_contact_update = any(value is not None for value in contact_fields.values())

    if has_contact_update:
        contact = organization.contacts.filter(is_primary=True).first()

        if not contact:
            contact = OrganizationContact.objects.create(
                organization=organization,
                is_primary=True,
                name="",
                email="",
            )

        if contact_fields["contact_name"] is not None:
            contact.name = contact_fields["contact_name"]

        if contact_fields["contact_email"] is not None:
            contact.email = contact_fields["contact_email"]

        if contact_fields["contact_phone"] is not None:
            contact.phone = contact_fields["contact_phone"]

        contact.save()

    # ---------------------------------------------------------
    # Subscription
    # ---------------------------------------------------------

    has_subscription_update = any(
        value is not None for value in subscription_fields.values()
    )

    if has_subscription_update:
        subscription = (
            OrganizationSubscription.objects.select_for_update()
            .filter(
                organization=organization,
                is_current=True,
                is_deleted=False,
            )
            .first()
        )

        if not subscription:
            raise ValueError("No current subscription found for this organization.")

        field_mapping = {
            "subscription_plan": "plan",
            "billing_cycle": "billing_cycle",
            "subscription_status": "status",
        }

        for frontend_field, value in subscription_fields.items():
            if value is not None:
                setattr(
                    subscription,
                    field_mapping[frontend_field],
                    value,
                )

        subscription.save()

    return organization


@transaction.atomic
def delete_organization(
    *,
    organization,
):
    """
    Soft delete the organization.

    Related records remain historically available through
    their organization relation.
    """

    organization.soft_delete()

    return organization


@transaction.atomic
def renew_subscription(
    *,
    organization,
    billing_cycle=None,
):
    """
    Renew the organization's current subscription.

    Rules:
    - If the current subscription is still active, the renewal is
      scheduled to start on the current subscription's expiry date.
    - If the current subscription has already expired, the renewal
      starts immediately.
    - The current subscription remains active until its expiry date.
    - Only one subscription can be current.
    - Future renewals are activated by the scheduled-subscription
      Celery task.
    """

    current_subscription = (
        organization.subscriptions.select_for_update()
        .select_related("plan")
        .filter(
            is_current=True,
            is_deleted=False,
        )
        .first()
    )

    if not current_subscription:
        raise ValueError("No current subscription found.")

    if billing_cycle is None:
        billing_cycle = current_subscription.billing_cycle

    if billing_cycle not in {
        BillingCycle.MONTHLY,
        BillingCycle.YEARLY,
    }:
        raise ValueError("Invalid billing cycle.")

    today = timezone.localdate()

    # =========================================================
    # DETERMINE START DATE AND STATUS
    # =========================================================

    current_is_active = (
        current_subscription.status == SubscriptionStatus.ACTIVE
        and current_subscription.expiry_date >= today
    )

    if current_is_active:
        # Current subscription continues until its expiry.
        start_date = current_subscription.expiry_date

        new_status = SubscriptionStatus.SCHEDULED
        new_is_current = False

    else:
        # No active subscription period remains.
        start_date = today

        new_status = SubscriptionStatus.ACTIVE
        new_is_current = True

    # =========================================================
    # CALCULATE EXPIRY DATE
    # =========================================================

    if billing_cycle == BillingCycle.MONTHLY:
        expiry_date = start_date + relativedelta(months=1)

    elif billing_cycle == BillingCycle.YEARLY:
        expiry_date = start_date + relativedelta(years=1)

    else:
        raise ValueError("Invalid billing cycle.")

    # =========================================================
    # CLOSE OLD SUBSCRIPTION ONLY IF IT IS ALREADY EXPIRED
    # =========================================================

    if not current_is_active:
        current_subscription.is_current = False

        if current_subscription.status == SubscriptionStatus.ACTIVE:
            current_subscription.status = SubscriptionStatus.EXPIRED

        current_subscription.save(
            update_fields=[
                "is_current",
                "status",
            ]
        )

    # =========================================================
    # CREATE RENEWAL
    # =========================================================

    new_subscription = OrganizationSubscription.objects.create(
        organization=organization,
        plan=current_subscription.plan,
        billing_cycle=billing_cycle,
        status=new_status,
        start_date=start_date,
        expiry_date=expiry_date,
        is_current=new_is_current,
    )

    return new_subscription


@transaction.atomic
def change_subscription_plan(
    *,
    organization,
    plan,
    billing_cycle,
):
    """
    Change an organization's subscription plan.

    Rules:

    1. If the current subscription is active and has not expired:
       - Keep the current subscription active.
       - Create the requested plan as scheduled.
       - Scheduled plan starts when the current subscription expires.

    2. If the current subscription is expired or does not exist:
       - Create the requested plan immediately as active.
       - Start date is today.

    3. Historical subscriptions are never overwritten.

    4. Concurrent subscription changes are serialized at the
       organization subscription level.
    """

    # =========================================================
    # VALIDATE PLAN
    # =========================================================

    if not isinstance(plan, Plan):
        raise ValueError("A valid plan is required.")

    if plan.status != "active" or plan.is_deleted:
        raise ValueError("The selected plan is not available.")

    # =========================================================
    # VALIDATE BILLING CYCLE
    # =========================================================

    if billing_cycle not in {
        BillingCycle.MONTHLY,
        BillingCycle.YEARLY,
    }:
        raise ValueError("Invalid billing cycle.")

    today = timezone.localdate()

    # =========================================================
    # LOCK CURRENT SUBSCRIPTION
    # =========================================================

    current_subscription = (
        OrganizationSubscription.objects.select_for_update()
        .select_related("plan")
        .filter(
            organization=organization,
            is_current=True,
            is_deleted=False,
        )
        .first()
    )

    # =========================================================
    # CASE 1
    # CURRENT SUBSCRIPTION IS STILL ACTIVE
    # =========================================================

    if (
        current_subscription
        and current_subscription.status == SubscriptionStatus.ACTIVE
        and current_subscription.expiry_date >= today
    ):

        # -----------------------------------------------------
        # SAME PLAN + SAME BILLING CYCLE
        # -----------------------------------------------------

        if (
            current_subscription.plan_id == plan.id
            and current_subscription.billing_cycle == billing_cycle
        ):
            raise ValueError(
                "The selected plan and billing cycle " "are already active."
            )

        # -----------------------------------------------------
        # PREVENT DUPLICATE SCHEDULED PLAN CHANGE
        # -----------------------------------------------------

        existing_scheduled = (
            OrganizationSubscription.objects.select_for_update()
            .filter(
                organization=organization,
                status=SubscriptionStatus.SCHEDULED,
                is_current=False,
                is_deleted=False,
            )
            .first()
        )

        if existing_scheduled:
            raise ValueError("A plan change is already scheduled.")

        # -----------------------------------------------------
        # CREATE SCHEDULED SUBSCRIPTION
        # -----------------------------------------------------

        start_date = current_subscription.expiry_date

        if billing_cycle == BillingCycle.MONTHLY:
            expiry_date = start_date + relativedelta(
                months=1,
            )
        else:
            expiry_date = start_date + relativedelta(
                years=1,
            )

        return OrganizationSubscription.objects.create(
            organization=organization,
            plan=plan,
            billing_cycle=billing_cycle,
            status=SubscriptionStatus.SCHEDULED,
            start_date=start_date,
            expiry_date=expiry_date,
            is_current=False,
        )

    # =========================================================
    # CASE 2
    # NO CURRENT ACTIVE SUBSCRIPTION
    # =========================================================

    if current_subscription:

        current_subscription.is_current = False

        if current_subscription.status == SubscriptionStatus.ACTIVE:
            current_subscription.status = SubscriptionStatus.EXPIRED

        current_subscription.save(
            update_fields=[
                "is_current",
                "status",
                "updated_at",
            ]
        )

    # =========================================================
    # CREATE IMMEDIATE ACTIVE SUBSCRIPTION
    # =========================================================

    start_date = today

    if billing_cycle == BillingCycle.MONTHLY:
        expiry_date = start_date + relativedelta(
            months=1,
        )
    else:
        expiry_date = start_date + relativedelta(
            years=1,
        )

    return OrganizationSubscription.objects.create(
        organization=organization,
        plan=plan,
        billing_cycle=billing_cycle,
        status=SubscriptionStatus.ACTIVE,
        start_date=start_date,
        expiry_date=expiry_date,
        is_current=True,
    )


@transaction.atomic
def activate_due_scheduled_subscriptions(
    *,
    as_of_date=None,
):
    """
    Activate scheduled subscriptions whose start date has arrived.

    Production rules:
    - Only scheduled subscriptions are eligible.
    - start_date must be <= as_of_date.
    - Scheduled subscriptions must not become current before their
      start date.
    - Only one subscription can remain current per organization.
    - The previous current subscription is expired before the
      scheduled subscription becomes active.
    - The operation is transaction-safe and idempotent.
    - Concurrent workers cannot activate the same subscription twice.

    Args:
        as_of_date:
            Optional date used for evaluation/testing.
            Defaults to the application's local date.

    Returns:
        int:
            Number of scheduled subscriptions activated.
    """

    today = as_of_date if as_of_date is not None else timezone.localdate()

    scheduled_subscriptions = (
        OrganizationSubscription.objects.select_for_update()
        .select_related(
            "organization",
            "plan",
        )
        .filter(
            status=SubscriptionStatus.SCHEDULED,
            is_current=False,
            is_deleted=False,
            start_date__lte=today,
        )
        .order_by(
            "organization_id",
            "start_date",
            "created_at",
        )
    )

    activated_count = 0

    for scheduled_subscription in scheduled_subscriptions:

        organization = scheduled_subscription.organization

        # -----------------------------------------------------
        # Lock the current subscription for this organization.
        #
        # This prevents concurrent Celery workers from changing
        # the same organization's subscription state at once.
        # -----------------------------------------------------

        current_subscription = (
            OrganizationSubscription.objects.select_for_update()
            .filter(
                organization=organization,
                is_current=True,
                is_deleted=False,
            )
            .first()
        )

        # -----------------------------------------------------
        # SAFETY CHECK
        #
        # If the current subscription is still valid beyond
        # the scheduled subscription's start date, the scheduled
        # subscription must remain scheduled.
        # -----------------------------------------------------

        if current_subscription:

            if current_subscription.expiry_date > scheduled_subscription.start_date:
                continue

            # -------------------------------------------------
            # Close the previous current subscription.
            # -------------------------------------------------

            current_subscription.is_current = False

            if current_subscription.status == SubscriptionStatus.ACTIVE:
                current_subscription.status = SubscriptionStatus.EXPIRED

            current_subscription.save(
                update_fields=[
                    "is_current",
                    "status",
                    "updated_at",
                ]
            )

        # -----------------------------------------------------
        # Re-check the scheduled record while inside the
        # transaction.
        #
        # This makes the operation idempotent even if another
        # process has already changed the record.
        # -----------------------------------------------------

        scheduled_subscription.refresh_from_db(
            fields=[
                "status",
                "is_current",
                "start_date",
            ]
        )

        if (
            scheduled_subscription.status != SubscriptionStatus.SCHEDULED
            or scheduled_subscription.is_current
            or scheduled_subscription.start_date > today
        ):
            continue

        # -----------------------------------------------------
        # Activate scheduled subscription.
        # -----------------------------------------------------

        scheduled_subscription.status = SubscriptionStatus.ACTIVE
        scheduled_subscription.is_current = True

        scheduled_subscription.save(
            update_fields=[
                "status",
                "is_current",
                "updated_at",
            ]
        )

        activated_count += 1

    return activated_count


@transaction.atomic
def cancel_subscription(
    *,
    organization,
):
    """
    Immediately cancel the organization's current subscription.

    Rules:
    - The current subscription is marked as cancelled.
    - It is no longer current.
    - Any future scheduled subscription for the organization
      is also cancelled.
    - Historical records are preserved.
    - Cancelled scheduled subscriptions must never be activated
      by the scheduled-subscription worker.
    """

    # =========================================================
    # LOCK CURRENT SUBSCRIPTION
    # =========================================================

    current_subscription = (
        OrganizationSubscription.objects.select_for_update()
        .filter(
            organization=organization,
            is_current=True,
            is_deleted=False,
        )
        .first()
    )

    # =========================================================
    # NO CURRENT SUBSCRIPTION
    # =========================================================

    if not current_subscription:
        raise ValueError("No current subscription found.")

    # =========================================================
    # ALREADY CANCELLED SAFETY CHECK
    # =========================================================

    if current_subscription.status == SubscriptionStatus.CANCELLED:
        raise ValueError("Subscription is already cancelled.")

    # =========================================================
    # CANCEL CURRENT SUBSCRIPTION
    # =========================================================

    current_subscription.status = SubscriptionStatus.CANCELLED

    current_subscription.is_current = False

    current_subscription.save(
        update_fields=[
            "status",
            "is_current",
            "updated_at",
        ]
    )

    # =========================================================
    # CANCEL FUTURE SCHEDULED SUBSCRIPTIONS
    # =========================================================

    (
        OrganizationSubscription.objects.select_for_update()
        .filter(
            organization=organization,
            status=SubscriptionStatus.SCHEDULED,
            is_current=False,
            is_deleted=False,
        )
        .update(
            status=SubscriptionStatus.CANCELLED,
        )
    )

    return current_subscription


@transaction.atomic
def start_new_subscription(
    *,
    organization,
    plan,
    billing_cycle,
):
    """
    Start a completely new subscription for an organization
    that currently has no active/current subscription.

    This is used after cancellation or expiry.
    """

    if not plan:
        raise ValueError("A valid plan is required.")

    if plan.status != "active":
        raise ValueError("The selected plan is not active.")

    if billing_cycle not in {
        BillingCycle.MONTHLY,
        BillingCycle.YEARLY,
    }:
        raise ValueError("Invalid billing cycle.")

    current_subscription = organization.subscriptions.filter(
        is_current=True,
    ).first()

    if current_subscription:
        raise ValueError("The organization already has a current subscription.")

    start_date = timezone.localdate()

    if billing_cycle == BillingCycle.MONTHLY:
        expiry_date = start_date + relativedelta(months=1)
    else:
        expiry_date = start_date + relativedelta(years=1)

    new_subscription = OrganizationSubscription.objects.create(
        organization=organization,
        plan=plan,
        billing_cycle=billing_cycle,
        status=SubscriptionStatus.ACTIVE,
        start_date=start_date,
        expiry_date=expiry_date,
        is_current=True,
    )

    return new_subscription
