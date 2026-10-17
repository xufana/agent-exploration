"""Ground truth of a configuration: the declared set.

Declared = what the agent's configuration says: system prompt, tools with
parameter schemas, and the DB collections behind them. The reachable set is
measured separately, from tool calls observed across repeated runs.
"""

from typing import Any

from pydantic import BaseModel
from tau2.agent.llm_agent import AGENT_INSTRUCTION, SYSTEM_PROMPT

from stand.build import agent_tools, build_environment
from stand.config import StandConfig


def declared(config: StandConfig) -> dict[str, Any]:
    env = build_environment(config)
    tools = agent_tools(env, config)
    return {
        "config": config.name,
        "domain": config.domain,
        "system_prompt": SYSTEM_PROMPT.format(
            agent_instruction=AGENT_INSTRUCTION, domain_policy=env.get_policy()
        ),
        "tools": [
            {
                "name": t.name,
                "description": t.openai_schema["function"]["description"],
                "parameters": t.openai_schema["function"]["parameters"],
                "mutates_state": env.tools.tool_mutates_state(t.name),
            }
            for t in tools
        ],
        # Tools that exist in the toolkit but are not shown to the agent upfront.
        "discoverable_tools": sorted(env.tools.get_discoverable_tools()),
        "resources": _db_collections(env.tools.db),
    }


def _db_collections(db: BaseModel | None) -> dict[str, dict[str, Any]]:
    """Record ids per top-level DB collection."""
    if db is None:
        return {}
    out = {}
    for name in type(db).model_fields:
        value = getattr(db, name)
        if isinstance(value, dict):
            out[name] = {"count": len(value), "ids": sorted(map(str, value))}
        elif isinstance(value, list):
            out[name] = {"count": len(value)}
    return out
