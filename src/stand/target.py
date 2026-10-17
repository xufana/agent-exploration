"""The agent under test, seen from the outside.

The prober only gets `send(text) -> reply`. Tool calls and tool results stay
inside and are recorded in `trace`, which is ground truth for scoring, never
input for the prober.
"""

from typing import Protocol

from tau2.data_model.message import (
    AssistantMessage,
    Message,
    MultiToolMessage,
    ToolCall,
    ToolMessage,
    UserMessage,
)
from tau2.orchestrator.orchestrator import DEFAULT_FIRST_AGENT_MESSAGE

from stand.build import AgentFactory, agent_tools, build_environment, llm_agent_factory
from stand.config import StandConfig


class Target(Protocol):
    """What probing code is allowed to depend on."""

    def reset(self) -> str: ...

    def send(self, text: str) -> str: ...


class TurnLimitExceeded(RuntimeError):
    pass


class BlackBoxAgent:
    def __init__(
        self,
        config: StandConfig,
        agent_factory: AgentFactory = llm_agent_factory,
        max_steps_per_turn: int = 30,
    ):
        self.config = config
        self.agent_factory = agent_factory
        self.max_steps_per_turn = max_steps_per_turn
        self.n_queries = 0
        self.reset()

    def reset(self) -> str:
        """Start a new conversation on a fresh DB. Returns the agent's greeting."""
        self.env = build_environment(self.config)
        self.tools = agent_tools(self.env, self.config)
        self.agent = self.agent_factory(self.tools, self.env.get_policy(), self.config)
        greeting = DEFAULT_FIRST_AGENT_MESSAGE.model_copy(deep=True)
        self._state = self.agent.get_init_state(message_history=[greeting])
        self.trace: list[Message] = [greeting]
        content: str = greeting.content
        return content

    def send(self, text: str) -> str:
        """One user turn: the agent may call tools any number of times, then replies."""
        self.n_queries += 1
        incoming = UserMessage(role="user", content=text)
        self.trace.append(incoming)
        for _ in range(self.max_steps_per_turn):
            reply, self._state = self.agent.generate_next_message(incoming, self._state)
            self.trace.append(reply)
            if not reply.is_tool_call():
                return reply.content or ""
            results = [self._execute(tc) for tc in reply.tool_calls]
            self.trace.extend(results)
            incoming = (
                results[0]
                if len(results) == 1
                else MultiToolMessage(role="tool", tool_messages=results)
            )
        raise TurnLimitExceeded(f"No text reply after {self.max_steps_per_turn} steps")

    def _execute(self, call: ToolCall) -> ToolMessage:
        # The env holds every domain tool; refuse the ones this config withholds.
        if call.name not in {t.name for t in self.tools}:
            return ToolMessage(
                id=call.id,
                role="tool",
                content=f"Error: Tool '{call.name}' not found.",
                requestor=call.requestor,
                error=True,
            )
        return self.env.get_response(call)

    # --- ground-truth views, not for the prober ---

    def tool_calls(self) -> list[ToolCall]:
        return [
            tc
            for m in self.trace
            if isinstance(m, AssistantMessage) and m.tool_calls
            for tc in m.tool_calls
        ]

    def transcript(self) -> list[dict[str, str | None]]:
        """The dialogue exactly as the prober saw it."""
        return [
            {"role": m.role, "content": m.content}
            for m in self.trace
            if isinstance(m, (UserMessage, AssistantMessage)) and not m.is_tool_call()
        ]

    def cost(self) -> float | None:
        costs = [m.cost for m in self.trace if isinstance(m, AssistantMessage) and m.cost]
        return sum(costs) if costs else None
