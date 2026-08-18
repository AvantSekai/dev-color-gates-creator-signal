import anthropic
import httpx
from fastapi.testclient import TestClient

import app.llm as llm_module
import app.routes.chat as chat_module
from app.llm import LLMConfigError, ask, get_client
from app.main import app

client = TestClient(app)


class FakeBlock:
    def __init__(self, type_, text=None):
        self.type = type_
        self.text = text


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeToolRunner:
    def __init__(self, messages):
        self._messages = messages

    def __iter__(self):
        return iter(self._messages)


class FakeClient:
    """Mimics client.beta.messages.tool_runner(...) and client.messages.create(...)
    without hitting the real API."""

    def __init__(self, messages, classify_verdict="FACT"):
        self.beta = self
        self.messages = self
        self._messages = messages
        self._classify_verdict = classify_verdict

    def tool_runner(self, **kwargs):
        return FakeToolRunner(self._messages)

    def create(self, **kwargs):
        return FakeMessage([FakeBlock("text", text=self._classify_verdict)])


def test_ask_tags_computed_when_a_tool_was_called_and_no_judgment_added():
    fake_client = FakeClient(
        [
            FakeMessage([FakeBlock("tool_use")]),
            FakeMessage([FakeBlock("text", text="reus.fx has the highest engagement rate.")]),
        ],
        classify_verdict="FACT",
    )
    result = ask("which creators get the most engagement?", client=fake_client)
    assert result["kind"] == "computed"
    assert "reus.fx" in result["answer"]
    assert result["sources"] == []  # FakeClient never runs the real tool functions


def test_ask_tags_grounded_opinion_when_tool_called_and_judgment_added():
    fake_client = FakeClient(
        [
            FakeMessage([FakeBlock("tool_use")]),
            FakeMessage(
                [FakeBlock("text", text="reus.fx has 40% engagement, which suggests a strong fit.")]
            ),
        ],
        classify_verdict="OPINION",
    )
    result = ask("would reus.fx fit a skincare brand?", client=fake_client)
    assert result["kind"] == "grounded_opinion"


def test_ask_tags_opinion_when_no_tool_was_called():
    fake_client = FakeClient([FakeMessage([FakeBlock("text", text="I think it could work well.")])])
    result = ask("would this creator fit a skincare brand?", client=fake_client)
    assert result["kind"] == "opinion"
    assert result["sources"] == []


def test_chat_route_rejects_empty_question():
    response = client.post("/api/chat", json={"question": "   "})
    assert response.status_code == 400


def test_chat_route_returns_computed_answer(monkeypatch):
    monkeypatch.setattr(
        chat_module,
        "ask",
        lambda q: {"answer": "top creator is x", "kind": "computed", "sources": [{"tool": "rank_creators"}]},
    )
    response = client.post("/api/chat", json={"question": "who has the most engagement?"})
    assert response.status_code == 200
    assert response.json() == {
        "answer": "top creator is x",
        "kind": "computed",
        "sources": [{"tool": "rank_creators"}],
    }


def test_chat_route_llm_error_returns_clear_500_not_silent(monkeypatch):
    def raise_connection_error(question: str):
        raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))

    monkeypatch.setattr(chat_module, "ask", raise_connection_error)
    response = client.post("/api/chat", json={"question": "who has the most engagement?"})
    assert response.status_code == 500
    assert "LLM request failed" in response.json()["detail"]


def test_get_client_raises_clear_error_when_api_key_unset(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(llm_module, "_client", None)
    try:
        get_client()
        assert False, "expected LLMConfigError"
    except LLMConfigError as exc:
        assert "ANTHROPIC_API_KEY" in str(exc)


def test_chat_route_missing_api_key_returns_clear_500_not_a_dropped_connection(monkeypatch):
    def raise_config_error(question: str):
        raise LLMConfigError("ANTHROPIC_API_KEY is not set.")

    monkeypatch.setattr(chat_module, "ask", raise_config_error)
    response = client.post("/api/chat", json={"question": "who has the most engagement?"})
    assert response.status_code == 500
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]
