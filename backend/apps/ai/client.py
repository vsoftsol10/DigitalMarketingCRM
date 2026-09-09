from django.conf import settings
from groq import Groq

from .exceptions import AIIntegrationError


class GroqAIClient:
    """
    Provider client responsible only for communicating
    with the Groq API.
    """

    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise AIIntegrationError(
                "Groq API key is not configured."
            )

        self.client = Groq(
            api_key=settings.GROQ_API_KEY,
        )

    def generate_caption(
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
        Generate a social media caption using Groq.
        """

        system_prompt = """
You are an expert social media copywriter.

Generate engaging, natural, platform-friendly social
media captions.

Follow the user's requested tone and length.

Return only the caption text.
Do not add explanations, labels, quotation marks,
or markdown formatting.
"""

        user_prompt = f"""
Create a social media caption.

User prompt:
{prompt or "Create an engaging caption based on the available context."}

Tone:
{tone}

Length:
{length}

Include emojis:
{include_emoji}

Include hashtags:
{include_hashtags}

Include call-to-action:
{include_cta}
"""

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt.strip(),
                    },
                    {
                        "role": "user",
                        "content": user_prompt.strip(),
                    },
                ],
                temperature=0.7,
            )

        except Exception as exc:
            raise AIIntegrationError(
                "Unable to generate caption using Groq."
            ) from exc

        content = (
            response.choices[0].message.content
            if response.choices
            else ""
        )

        if not content:
            raise AIIntegrationError(
                "Groq returned an empty caption."
            )

        return content.strip()