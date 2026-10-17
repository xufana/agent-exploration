"""Agent configurations of the testbed.

A configuration fixes everything that defines the agent under test: the τ-bench
domain (policy + tools + DB), the LLM behind it, and which subset of the
domain's tools the agent is given. Varying configurations of an existing
benchmark is cheaper than building new agents (see README, "Risks").
"""

import os
from dataclasses import dataclass, field, replace
from typing import Any

DEFAULT_AGENT_LLM = os.getenv("AGENT_LLM", "gpt-4.1-mini")
DEFAULT_AGENT_API_BASE = os.getenv("AGENT_API_BASE") or None


@dataclass(frozen=True)
class StandConfig:
    name: str
    domain: str
    agent_llm: str = DEFAULT_AGENT_LLM
    agent_llm_args: dict[str, Any] = field(default_factory=lambda: {"temperature": 0.0})
    # OpenAI-compatible endpoint (vLLM, Ollama, proxy); use with agent_llm="openai/<model>".
    # The key comes from AGENT_API_KEY and is never stored in the config.
    agent_api_base: str | None = DEFAULT_AGENT_API_BASE
    # Task whose initial_state seeds the environment; None keeps the pristine DB.
    task_id: str | None = None
    # Restrict the agent's toolset to these names; None means all domain tools.
    tools_include: tuple[str, ...] | None = None
    # Drop every tool that mutates the DB.
    readonly: bool = False

    def with_llm(self, llm: str) -> "StandConfig":
        return replace(self, agent_llm=llm)


CONFIGS: dict[str, StandConfig] = {
    c.name: c
    for c in [
        StandConfig(name="retail", domain="retail"),
        StandConfig(name="retail-readonly", domain="retail", readonly=True),
        StandConfig(name="airline", domain="airline"),
        StandConfig(name="telecom", domain="telecom"),
        StandConfig(name="mock", domain="mock"),
    ]
}


def get_config(name: str) -> StandConfig:
    if name not in CONFIGS:
        raise KeyError(f"Unknown config {name!r}. Available: {sorted(CONFIGS)}")
    return CONFIGS[name]
