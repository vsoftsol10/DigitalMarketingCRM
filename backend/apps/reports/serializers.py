from rest_framework import serializers

from apps.social_accounts.models import SocialPlatform


class MetaAdsRowSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_leads = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
    )


class InsightsReportPreviewSerializer(serializers.Serializer):
    organization_id = serializers.CharField(max_length=20)
    social_account_id = serializers.UUIDField()
    platform = serializers.ChoiceField(
        choices=(SocialPlatform.INSTAGRAM, SocialPlatform.FACEBOOK),
    )
    since = serializers.DateField()
    until = serializers.DateField()
    mode = serializers.ChoiceField(choices=("current", "add_ads"))
    meta_ads = MetaAdsRowSerializer(many=True, required=False, default=list, max_length=5)

    def validate(self, attrs):
        if attrs["since"] > attrs["until"]:
            raise serializers.ValidationError({"since": "since must be on or before until."})
        if attrs["mode"] == "current" and attrs["meta_ads"]:
            raise serializers.ValidationError({
                "meta_ads": "Meta Ads rows are only accepted for Add Data & Export."
            })
        return attrs


class InsightsReportRenderSerializer(serializers.Serializer):
    render_token = serializers.CharField(max_length=2048)
    html = serializers.CharField(max_length=1_000_000, trim_whitespace=False)

    def validate_html(self, value):
        if 'id="report-document"' not in value or "<html" not in value.lower():
            raise serializers.ValidationError("Report markup is invalid.")
        return value
