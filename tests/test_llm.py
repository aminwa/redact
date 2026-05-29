import json
from unittest.mock import MagicMock, patch
from redact.core.llm import LLMEngine
from redact.core.entities import EntityType


def _mock_response(items: list[dict]):
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(items))]
    return msg


def test_llm_extracts_person():
    with patch("redact.core.llm._get_client") as mock:
        mock.return_value.messages.create.return_value = _mock_response([
            {"type": "PERSON", "text": "Alice", "start": 0, "end": 5}
        ])
        ents = LLMEngine().extract("Alice works here")
    assert any(e.type == EntityType.PERSON for e in ents)


def test_llm_extracts_email():
    with patch("redact.core.llm._get_client") as mock:
        mock.return_value.messages.create.return_value = _mock_response([
            {"type": "EMAIL", "text": "a@b.com", "start": 9, "end": 16}
        ])
        ents = LLMEngine().extract("contact: a@b.com")
    assert any(e.type == EntityType.EMAIL for e in ents)


def test_llm_skips_unknown_types():
    with patch("redact.core.llm._get_client") as mock:
        mock.return_value.messages.create.return_value = _mock_response([
            {"type": "ANIMAL", "text": "cat", "start": 0, "end": 3}
        ])
        ents = LLMEngine().extract("cat sat here")
    assert len(ents) == 0


def test_llm_handles_malformed_json():
    with patch("redact.core.llm._get_client") as mock:
        msg = MagicMock()
        msg.content = [MagicMock(text="not valid json at all")]
        mock.return_value.messages.create.return_value = msg
        ents = LLMEngine().extract("some text")
    assert ents == []


def test_llm_strips_markdown_fences():
    with patch("redact.core.llm._get_client") as mock:
        payload = "```json\n" + json.dumps([
            {"type": "SSN", "text": "123-45-6789", "start": 5, "end": 16}
        ]) + "\n```"
        msg = MagicMock()
        msg.content = [MagicMock(text=payload)]
        mock.return_value.messages.create.return_value = msg
        ents = LLMEngine().extract("ssn: 123-45-6789")
    assert any(e.type == EntityType.SSN for e in ents)


def test_llm_multiple_entities():
    with patch("redact.core.llm._get_client") as mock:
        mock.return_value.messages.create.return_value = _mock_response([
            {"type": "PERSON", "text": "Bob",         "start": 0,  "end": 3},
            {"type": "EMAIL",  "text": "bob@test.com","start": 12, "end": 24},
        ])
        ents = LLMEngine().extract("Bob, email: bob@test.com")
    assert len(ents) == 2
