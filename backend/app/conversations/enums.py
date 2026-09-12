from enum import Enum


class ChatStatus(str, Enum):
    OPEN = "OPEN"
    DELETE = "DELETE"
    ARCHIVED = "ARCHIVED"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"  


class MediaType(str, Enum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"