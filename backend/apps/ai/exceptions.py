class AIIntegrationError(Exception):
    """Base exception for AI provider integration errors."""


class AICaptionGenerationError(AIIntegrationError):
    """Raised when AI caption generation fails."""