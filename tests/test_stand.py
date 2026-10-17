"""Testbed checks that need no LLM: a scripted agent stands in for the model."""

from collections.abc import Callable
from dataclasses import replace
from typing import Any

import pytest
from tau2.data_model.message import AssistantMessage, ToolCall, ToolMessage

import stand
from stand.config import get_config
from stand.ground_truth import declared
from stand.target import BlackBoxAgent

pytestmark = pytest.mark.skipif(
    stand.TAU2_DATA_DIR is None, reason="tau2 data missing: git submodule update --init"
)


class ScriptedAgent:
    """Calls the given tools once on the user's turn, then replies with the last result."""

    def __init__(self, calls: list[ToolCall]) -> None:
        self.calls = calls

    def get_init_state(self, message_history: Any = None) -> dict[str, bool]:
        return {"done": False}

    def generate_next_message(
        self, message: Any, state: dict[str, bool]
    ) -> tuple[AssistantMessage, dict[str, bool]]:
        if not state["done"]:
            state["done"] = True
            return AssistantMessage(role="assistant", tool_calls=self.calls), state
        assert isinstance(message, ToolMessage)
        return AssistantMessage(role="assistant", content=message.content), state


def scripted(*calls: ToolCall) -> Callable[..., ScriptedAgent]:
    return lambda tools, policy, config: ScriptedAgent(list(calls))


def test_declared_retail() -> None:
    data = declared(get_config("retail"))
    names = {t["name"] for t in data["tools"]}
    assert {"get_user_details", "cancel_pending_order"} <= names
    assert all("properties" in t["parameters"] for t in data["tools"])
    assert data["resources"]["users"]["count"] > 0
    assert "<policy>" in data["system_prompt"]


def test_readonly_drops_mutating_tools() -> None:
    data = declared(get_config("retail-readonly"))
    assert data["tools"]
    assert not any(t["mutates_state"] for t in data["tools"])


def test_tool_calls_are_hidden_but_traced() -> None:
    call = ToolCall(id="1", name="calculate", arguments={"expression": "2 + 2"})
    target = BlackBoxAgent(get_config("retail"), agent_factory=scripted(call))
    assert target.send("what is 2+2?") == "4.0"
    assert [tc.name for tc in target.tool_calls()] == ["calculate"]
    assert all(m["content"] for m in target.transcript())
    assert target.n_queries == 1


def test_withheld_tool_is_refused() -> None:
    cfg = replace(get_config("retail"), tools_include=("calculate",))
    call = ToolCall(
        id="1", name="cancel_pending_order", arguments={"order_id": "#W0000000", "reason": "x"}
    )
    target = BlackBoxAgent(cfg, agent_factory=scripted(call))
    db_hash = target.env.get_db_hash()
    assert "not found" in target.send("cancel my order")
    assert target.env.get_db_hash() == db_hash
