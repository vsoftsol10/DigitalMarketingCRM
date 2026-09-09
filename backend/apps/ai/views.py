from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import success_response

from .serializers import AICaptionGenerateSerializer
from .services import AICaptionService


class AICaptionGenerateAPIView(APIView):
    """
    Generate AI-powered social media caption suggestions.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        serializer = AICaptionGenerateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        validated_data = serializer.validated_data

        service = AICaptionService()

        captions = service.generate_captions(
            prompt=validated_data.get(
                "prompt",
                "",
            ),
            tone=validated_data["tone"],
            length=validated_data["length"],
            include_emoji=validated_data["include_emoji"],
            include_hashtags=validated_data["include_hashtags"],
            include_cta=validated_data["include_cta"],
        )

        titles = [
            "Professional",
            "Engaging",
            "Promotional",
        ]

        suggestions = [
            {
                "id": index + 1,
                "title": titles[index],
                "caption": caption,
            }
            for index, caption in enumerate(captions)
        ]

        return success_response(
            data=suggestions,
            message="AI captions generated successfully.",
            status_code=status.HTTP_200_OK,
        )