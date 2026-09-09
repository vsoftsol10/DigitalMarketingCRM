from rest_framework import serializers


class AICaptionGenerateSerializer(serializers.Serializer):
    """
    Validate AI caption generation requests.
    """

    prompt = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000,
    )

    tone = serializers.ChoiceField(
        choices=[
            "PROFESSIONAL",
            "FRIENDLY",
            "CASUAL",
            "PROMOTIONAL",
            "FUNNY",
            "INSPIRATIONAL",
        ],
    )

    length = serializers.ChoiceField(
        choices=[
            "SHORT",
            "MEDIUM",
            "LONG",
        ],
    )

    include_emoji = serializers.BooleanField(
        default=True,
    )

    include_hashtags = serializers.BooleanField(
        default=True,
    )

    include_cta = serializers.BooleanField(
        default=True,
    )