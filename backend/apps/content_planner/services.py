from django.db import transaction

from .models import ContentIdea


@transaction.atomic
def create_content_idea(
    *,
    validated_data,
):
    """
    Create a new content idea.

    All write operations are kept inside the service layer so
    API views remain thin and business logic stays centralized.
    """

    organization = validated_data["organization"]

    if organization.is_deleted:
        raise ValueError(
            "The selected organization is not available."
        )

    return ContentIdea.objects.create(
        **validated_data,
    )


@transaction.atomic
def update_content_idea(
    *,
    content_idea,
    validated_data,
):
    """
    Update an existing content idea.
    """

    if content_idea.is_deleted:
        raise ValueError(
            "The content idea is not available."
        )

    organization = validated_data.get(
        "organization",
    )

    if organization and organization.is_deleted:
        raise ValueError(
            "The selected organization is not available."
        )

    for field, value in validated_data.items():
        setattr(
            content_idea,
            field,
            value,
        )

    content_idea.save()

    return content_idea


@transaction.atomic
def delete_content_idea(
    *,
    content_idea,
):
    """
    Soft-delete a content idea.

    The record is preserved for historical/audit purposes.
    """

    if content_idea.is_deleted:
        raise ValueError(
            "The content idea is already deleted."
        )

    content_idea.soft_delete()

    return content_idea