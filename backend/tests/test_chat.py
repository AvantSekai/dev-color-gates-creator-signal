import anthropic
import httpx
from fastapi.testclient import TestClient

import app.routes.chat as chat_module
from app.llm import ask
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
    """Mimics client.beta.messages.tool_runner(...) without hitting the real API."""

    def __init__(self, messages):
        self.beta = self
        self.messages = self
        self._messages = messages

    def tool_runner(self, **kwargs):
        return FakeToolRunner(self._messages)


def test_ask_tags_computed_when_a_tool_was_called():
    fake_client = FakeClient(
        [
            FakeMessage([FakeBlock("tool_use")]),
            FakeMessage([FakeBlock("text", text="reus.fx has the highest engagement rate.")]),
        ]
    )
    result = ask("which creators get the most engagement?", client=fake_client)
    assert result["kind"] == "computed"
    assert "reus.fx" in result["answer"]


def test_ask_tags_opinion_when_no_tool_was_called():
    fake_client = FakeClient([FakeMessage([FakeBlock("text", text="I think it could work well.")])])
    result = ask("would this creator fit a skincare brand?", client=fake_client)
    assert result["kind"] == "opinion"


def test_chat_route_rejects_empty_question():
    response = client.post("/api/chat", json={"question": "   "})
    assert response.status_code == 400


def test_chat_route_returns_computed_answer(monkeypatch):
    monkeypatch.setattr(chat_module, "ask", lambda q: {"answer": "top creator is x", "kind": "computed"})
    response = client.post("/api/chat", json={"question": "who has the most engagement?"})
    assert response.status_code == 200
    assert response.json() == {"answer": "top creator is x", "kind": "computed"}


def test_chat_route_llm_error_returns_clear_500_not_silent(monkeypatch):
    def raise_connection_error(question: str):
        raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))

    monkeypatch.setattr(chat_module, "ask", raise_connection_error)
    response = client.post("/api/chat", json={"question": "who has the most engagement?"})
    assert response.status_code == 500
    assert "LLM request failed" in response.json()["detail"]
