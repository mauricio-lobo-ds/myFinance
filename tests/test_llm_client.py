import json
from unittest.mock import MagicMock, patch
import ai.llm_client as llm


def _make_response(content: str) -> MagicMock:
    resp = MagicMock()
    resp.choices[0].message.content = content
    return resp


def test_ask_llm_injects_today_into_prompt():
    with patch.object(llm, "_client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_response('{"intent":"invalido"}')
        llm.ask_llm("oi", "2026-05-11")
        call_args = mock_client.chat.completions.create.call_args
        system_msg = call_args.kwargs["messages"][0]["content"]
        assert "2026-05-11" in system_msg


def test_ask_llm_returns_raw_content():
    with patch.object(llm, "_client") as mock_client:
        payload = '{"intent": "registrar", "valido": true, "valor": 35.0}'
        mock_client.chat.completions.create.return_value = _make_response(payload)
        result = llm.ask_llm("Almoço 35", "2026-05-11")
        assert result == payload


def test_ask_llm_passes_user_message():
    with patch.object(llm, "_client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_response('{"intent":"invalido"}')
        llm.ask_llm("Netflix 45,90", "2026-05-11")
        messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        user_msg = next(m for m in messages if m["role"] == "user")
        assert user_msg["content"] == "Netflix 45,90"


def test_ask_llm_uses_correct_model():
    with patch.object(llm, "_client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_response('{"intent":"invalido"}')
        llm.ask_llm("teste", "2026-05-11")
        model = mock_client.chat.completions.create.call_args.kwargs["model"]
        assert model == "openai/gpt-4o-mini"
