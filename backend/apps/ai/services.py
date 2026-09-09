from .client import GroqAIClient
from .exceptions import AICaptionGenerationError


class AICaptionService:
    """
    Application service responsible for generating
    social media captions.

    Provider-specific communication is delegated to
    GroqAIClient.
    """

    def __init__(self):
        self.client = GroqAIClient()

    def generate_captions(
        self,
        *,
        prompt,
        tone,
        length,
        include_emoji,
        include_hashtags,
        include_cta,
    ):
        """
        Generate multiple caption suggestions.
        """

        try:
            captions = []

            variations = [
                "Create a strong primary version.",
                "Create a more engaging and audience-focused version.",
                "Create a more promotional and conversion-focused version.",
            ]

            for variation in variations:
                caption = self.client.generate_caption(
                    prompt=f"""
{variation}

Original request:
{prompt}
""",
                    tone=tone,
                    length=length,
                    include_emoji=include_emoji,
                    include_hashtags=include_hashtags,
                    include_cta=include_cta,
                )

                captions.append(caption)

            return captions

        except Exception as exc:
            if isinstance(exc, AICaptionGenerationError):
                raise

            raise AICaptionGenerationError(
                "Unable to generate AI caption suggestions."
            ) from exc