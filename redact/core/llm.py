import json
import os
import anthropic
from .entities import Entity, EntityType

_client: anthropic.Anthropic | None = None

_SYSTEM = (
    "You are a PII detection engine. Given text, identify all personally identifiable information.\n"
    "Return a JSON array of objects with fields: type, text, start, end.\n"
    "Types: PERSON, EMAIL, PHONE, ORG, LOCATION, CARD, SSN, DATE.\n"
    "start and end are character offsets into the original text.\n"
    "Return ONLY the JSON array, no explanation, no markdown fences."
)


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


class LLMEngine:
    def __init__(self, model: str = "claude-haiku-4-5-20251001"):
        self._model = model

    def extract(self, text: str) -> list[Entity]:
        response = _get_client().messages.create(
            model=self._model,
            max_tokens=2048,
            system=_SYSTEM,
            messages=[{"role": "user", "content": text}],
        )

        raw = response.content[0].text.strip().strip("```json").strip("```").strip()

        try:
            items = json.loads(raw)
        except json.JSONDecodeError:
            return []

        entities: list[Entity] = []
        for item in items:
            try:
                etype = EntityType(item["type"])
            except (ValueError, KeyError):
                continue
            entities.append(Entity(
                type=etype,
                text=str(item.get("text", "")),
                start=int(item.get("start", 0)),
                end=int(item.get("end", 0)),
                source="llm",
            ))

        return entities
