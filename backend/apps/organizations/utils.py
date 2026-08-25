from django.utils.text import slugify

from .models import Organization


def generate_unique_slug(
    name,
    instance=None,
):
    base_slug = slugify(name)

    if not base_slug:
        base_slug = "organization"

    slug = base_slug
    counter = 1

    queryset = Organization.objects.all()

    if instance is not None:
        queryset = queryset.exclude(pk=instance.pk)

    while queryset.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug
