import aiohttp


class DuckChatException(aiohttp.client.ClientError):
    """Base exception class for duck_chat."""


class RatelimitException(DuckChatException):
    """Raised for rate limit exceeded errors during API requests."""


class ConversationLimitException(DuckChatException):
    """Raised for conversation limit during API requests to AI endpoint."""


class ChallengeException(DuckChatException):
    """Raised for challenge failed"""


class BadRequestException(DuckChatException):
    """Raised for bad request to API (model not support image etc.)"""


ERROR_MAPPING: dict[str, type[DuckChatException]] = {
    "ERR_CONVERSATION_LIMIT": ConversationLimitException,
    "ERR_CHALLENGE": ChallengeException,
    "ERR_BAD_REQUEST": BadRequestException,
}
