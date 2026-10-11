import secrets
from dataclasses import dataclass, field

from presidio_analyzer import AnalyzerEngine


PII_ENTITIES = [
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
]


@dataclass
class PIIVault:
    # Never add this object or its contents to LangGraph state.
    _values: dict[str, str] = field(default_factory=dict)

    def tokenize(self, value: str, entity_type: str) -> str:
        token = f"[PII_{entity_type}_{secrets.token_hex(16)}]"
        self._values[token] = value
        return token

    def resolve(self, token: str) -> str:
        try:
            return self._values[token]
        except KeyError:
            raise ValueError("Unknown or expired PII reference") from None

    def clear(self) -> None:
        self._values.clear()


class PIIProtector:
    def __init__(self) -> None:
        self.analyzer = AnalyzerEngine()

    def protect(
        self,
        text: str,
        vault: PIIVault,
    ) -> str:
        findings = self.analyzer.analyze(
            text=text,
            language="en",
            entities=PII_ENTITIES,
        )

        # Replace from right to left so earlier offsets stay valid.
        safe_text = text

        for finding in sorted(
            findings,
            key=lambda item: item.start,
            reverse=True,
        ):
            original = safe_text[finding.start:finding.end]

            token = vault.tokenize(
                original,
                finding.entity_type,
            )

            safe_text = (
                safe_text[:finding.start]
                + token
                + safe_text[finding.end:]
            )

        return safe_text


protector = PIIProtector()
vault = PIIVault()

try:
    safe_query = protector.protect(
        "Find the account for alex@example.com",
        vault,
    )

    # Only safe_query goes to the LLM workflow.
    print(safe_query)

    # Trusted backend code can resolve a token when required.
    # Never pass the resolved value back to an LLM.
finally:
    vault.clear()