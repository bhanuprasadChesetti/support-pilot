

from enum import StrEnum



class Providers(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    TOGETHER = "together"
    NVIDIA = "nvidia"