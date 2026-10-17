"""Construct τ-bench objects (environment, toolset, agent) from a StandConfig."""

import os
from collections.abc import Callable

import litellm
from tau2.agent.base_agent import HalfDuplexAgent
from tau2.agent.llm_agent import LLMAgent
from tau2.data_model.tasks import Task
from tau2.environment.environment import Environment
from tau2.environment.tool import Tool
from tau2.registry import registry

from stand.config import StandConfig

AgentFactory = Callable[[list[Tool], str, StandConfig], HalfDuplexAgent]


def build_environment(config: StandConfig) -> Environment:
    """A fresh environment with its own copy of the domain DB."""
    env = registry.get_env_constructor(config.domain)()
    if config.task_id is not None:
        task = _get_task(config.domain, config.task_id)
        if task.initial_state is not None:
            env.set_state(
                initialization_data=task.initial_state.initialization_data,
                initialization_actions=task.initial_state.initialization_actions,
                message_history=[],
            )
    return env


def agent_tools(env: Environment, config: StandConfig) -> list[Tool]:
    """The tools the agent is given (the declared set), after config filters."""
    tools: list[Tool] = env.get_tools()
    if config.tools_include is not None:
        unknown = set(config.tools_include) - {t.name for t in tools}
        if unknown:
            raise ValueError(f"Unknown tools for domain {config.domain}: {unknown}")
        tools = [t for t in tools if t.name in config.tools_include]
    if config.readonly:
        tools = [t for t in tools if not env.tools.tool_mutates_state(t.name)]
    return tools


def llm_agent_factory(tools: list[Tool], policy: str, config: StandConfig) -> HalfDuplexAgent:
    llm_args = dict(config.agent_llm_args)
    if config.agent_api_base:
        llm_args["api_base"] = config.agent_api_base
        llm_args["api_key"] = os.getenv("AGENT_API_KEY") or "EMPTY"
        # Self-hosted models have no LiteLLM price entry; count them as free.
        litellm.register_model(
            {
                config.agent_llm: {
                    "input_cost_per_token": 0.0,
                    "output_cost_per_token": 0.0,
                    "litellm_provider": "openai",
                    "mode": "chat",
                }
            }
        )
    return LLMAgent(
        tools=tools,
        domain_policy=policy,
        llm=config.agent_llm,
        llm_args=llm_args,
    )


def _get_task(domain: str, task_id: str) -> Task:
    tasks = registry.get_tasks_loader(domain)(None)
    for task in tasks:
        if task.id == task_id:
            return task
    raise KeyError(f"Task {task_id!r} not found in domain {domain}")
