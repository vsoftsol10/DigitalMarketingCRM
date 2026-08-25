from django.db import models

from apps.common.models import BaseModel


class BrandAssetType(models.TextChoices):
    LOGO = "logo", "Logo"
    COVER = "cover", "Cover"
    FAVICON = "favicon", "Favicon"
    OTHER = "other", "Other"


class BrandAsset(BaseModel):
    """
    Files/assets belonging to an organization brand.

    The current frontend mainly uses logo_color and does not require
    uploaded brand assets yet, but keeping this domain separate makes
    future brand management extensible.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="brand_assets",
    )

    asset_type = models.CharField(
        max_length=20,
        choices=BrandAssetType.choices,
    )

    name = models.CharField(
        max_length=255,
    )

    file = models.FileField(
        upload_to="organizations/brand-assets/",
    )

    is_primary = models.BooleanField(
        default=False,
    )

    class Meta:
        db_table = "brand_assets"
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=[
                    "organization",
                    "asset_type",
                ],
                name="brand_org_type_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.organization.name} - "
            f"{self.name}"
        )