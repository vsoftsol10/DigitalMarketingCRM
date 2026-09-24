from django.db import models

from apps.common.models import BaseModel
from apps.organizations.models import Organization
from apps.social_accounts.models import SocialAccount


class ContentIdeaPlatform(models.TextChoices):
    INSTAGRAM = "INSTAGRAM", "Instagram"
    FACEBOOK = "FACEBOOK", "Facebook"
    YOUTUBE = "YOUTUBE", "YouTube"
    LINKEDIN = "LINKEDIN", "LinkedIn"
    X = "X", "X (Twitter)"


class ContentIdeaType(models.TextChoices):
    POST = "POST", "Post"
    REEL = "REEL", "Reel"
    STORY = "STORY", "Story"


class ContentIdea(BaseModel):
    """
    Content planning idea belonging to an organization.

    Content ideas are maintained independently from actual published
    posts. The idea may later be used to create a post through the
    post creation workflow.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="content_ideas",
        db_index=True,
    )

    caption = models.CharField(
        max_length=2200,
    )

    description = models.TextField(
        blank=True,
    )

    # Deprecated legacy metadata. Retained in the database so pre-redesign
    # records are not silently discarded; new API writes do not expose it.
    platform = models.CharField(
        max_length=20,
        choices=ContentIdeaPlatform.choices,
        db_index=True,
        null=True,
        blank=True,
    )

    content_type = models.CharField(
        max_length=20,
        choices=ContentIdeaType.choices,
        db_index=True,
    )

    # Deprecated legacy metadata. See ``platform`` above.
    campaign_goal = models.CharField(
        max_length=30,
        db_index=True,
        null=True,
        blank=True,
    )

    target_publish_date = models.DateField(
        db_index=True,
    )

    target_publish_time = models.TimeField(
        null=True,
        blank=True,
    )

    selected_social_accounts = models.ManyToManyField(
        SocialAccount,
        related_name="content_ideas",
        blank=True,
    )

    class Meta:
        db_table = "content_ideas"

        ordering = [
            "target_publish_date",
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "organization",
                    "target_publish_date",
                ],
                name="content_idea_org_date_idx",
            ),
            models.Index(
                fields=[
                    "platform",
                    "target_publish_date",
                ],
                name="content_idea_platform_date_idx",
            ),
            models.Index(
                fields=[
                    "campaign_goal",
                    "target_publish_date",
                ],
                name="content_idea_goal_date_idx",
            ),
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.caption}"
