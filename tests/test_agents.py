"""Unit tests for llm_agents.py — pure logic only (no API calls, no keys)."""

from llm_agents import LLMAgent, add_parameters_schema

# ---------------------------------------------------------------------------
# Tool schema decorator
# ---------------------------------------------------------------------------


def test_add_parameters_schema_attaches_metadata():
    @add_parameters_schema(city={"type": "string", "description": "City name"})
    def weather(city):
        """Get weather for a city."""
        return f"sunny in {city}"

    assert weather.parameters_schema == {"city": {"type": "string", "description": "City name"}}


def test_schema_marks_required_fields():
    @add_parameters_schema(
        city={"type": "string", "description": "City"},
        days={"type": "integer", "description": "Days", "default": 3},
    )
    def forecast(city, days=3):
        return city

    agent = LLMAgent(tools=[forecast])
    schemas = agent._get_tool_schemas()
    assert schemas is not None
    fn = schemas[0]["function"]
    assert fn["name"] == "forecast"
    assert fn["description"] == "Get weather for a city." or "forecast" in fn["description"]
    assert "city" in fn["parameters"]["required"]
    assert "days" not in fn["parameters"]["required"]


# ---------------------------------------------------------------------------
# Agent basics
# ---------------------------------------------------------------------------


def test_agent_defaults():
    agent = LLMAgent()
    assert agent.model.startswith("gemini/") or "/" in agent.model
    assert agent.tools == []
    assert "travel" in agent.system_prompt.lower()


def test_add_tool_and_set_prompt():
    agent = LLMAgent()

    def dummy():
        """Do nothing useful."""
        return "ok"

    agent.add_tool(dummy)
    assert dummy in agent.tools

    agent.set_system_prompt("You are a drone pilot.")
    assert agent.get_system_prompt() == "You are a drone pilot."


def test_no_tools_returns_none_schema():
    agent = LLMAgent()
    assert agent._get_tool_schemas() is None


def test_tool_schema_uses_docstring(monkeypatch):
    @add_parameters_schema(x={"type": "number"})
    def add_one(x):
        """Add one to the input."""
        return x + 1

    agent = LLMAgent(tools=[add_one])
    fn = agent._get_tool_schemas()[0]["function"]
    assert fn["description"] == "Add one to the input."


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------


def test_execute_tool_by_name():
    @add_parameters_schema(a={"type": "number"}, b={"type": "number"})
    def add(a, b):
        return a + b

    agent = LLMAgent(tools=[add])
    assert agent._execute_tool("add", a=2, b=3) == 5


def test_execute_unknown_tool_returns_error():
    agent = LLMAgent()
    assert "not found" in agent._execute_tool("nope")


def test_execute_tool_catches_exceptions():
    @add_parameters_schema()
    def boom():
        raise RuntimeError("kaput")

    agent = LLMAgent(tools=[boom])
    result = agent._execute_tool("boom")
    assert "Error executing boom" in result
    assert "kaput" in result


# ---------------------------------------------------------------------------
# Conversation bookkeeping (mocked API)
# ---------------------------------------------------------------------------


class FakeResponse:
    """Minimal litellm-compatible completion response."""

    def __init__(self, text):
        self.choices = [
            type("C", (), {"message": type("M", (), {"content": text, "tool_calls": None})()})
        ]


def _fake_completion(model, messages, **kwargs):
    return FakeResponse("mock response")


def test_chat_with_debug_tracks_history(monkeypatch):
    """chat_with_debug must append user messages and record tool metadata without calling the API."""
    import llm_agents

    monkeypatch.setattr(llm_agents.litellm, "completion", _fake_completion)
    agent = LLMAgent()

    response, debug = agent.chat_with_debug("Hello there")
    assert response == "mock response"
    assert agent.conversation_history[-1]["role"] == "assistant"
    assert any("Hello there" in line for line in debug)


def test_clear_memory_resets_history(monkeypatch):
    import llm_agents

    monkeypatch.setattr(llm_agents.litellm, "completion", _fake_completion)
    agent = LLMAgent()

    agent.chat_with_debug("first", clear_memory=True)
    agent.chat_with_debug("second", clear_memory=True)
    # With clear_memory=True the history holds only the latest exchange
    assert len(agent.conversation_history) == 2  # user + assistant
    assert agent.conversation_history[0]["content"] == "second"
