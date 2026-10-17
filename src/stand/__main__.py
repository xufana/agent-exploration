"""Testbed CLI.

python -m stand configs                  # list configurations
python -m stand declared retail          # dump the declared set to data/ground_truth/
python -m stand chat retail              # talk to the agent as the user
"""

import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import typer

from stand.config import CONFIGS, get_config
from stand.ground_truth import declared as get_declared
from stand.target import BlackBoxAgent

ROOT = Path(__file__).resolve().parents[2]
GROUND_TRUTH_DIR = ROOT / "data" / "ground_truth"
RUNS_DIR = ROOT / "experiments" / "runs"

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def configs() -> None:
    """List testbed configurations."""
    for c in CONFIGS.values():
        print(f"{c.name:20} domain={c.domain:10} llm={c.agent_llm}")


@app.command()
def declared(config: str, out_dir: Path = GROUND_TRUTH_DIR) -> None:
    """Write the declared set (prompt, tools, schemas, DB ids) of a configuration."""
    data = get_declared(get_config(config))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{config}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"{len(data['tools'])} tools -> {path}")


@app.command()
def chat(
    config: str,
    llm: str | None = None,
    api_base: str | None = None,
    show_tools: bool = False,
) -> None:
    """Interactive chat as the user. Commands: /trace, /reset, /quit."""
    cfg = get_config(config)
    if llm:
        cfg = cfg.with_llm(llm)
    if api_base:
        cfg = replace(cfg, agent_api_base=api_base)
    target = BlackBoxAgent(cfg)
    print(f"[{cfg.name} · {cfg.agent_llm}] agent: {target.reset()}")
    try:
        while True:
            text = input("you> ").strip()
            if not text:
                continue
            if text == "/quit":
                break
            if text == "/reset":
                _save(target)
                print(f"agent: {target.reset()}")
                continue
            if text == "/trace":
                for tc in target.tool_calls():
                    print(f"  {tc.name}({json.dumps(tc.arguments, ensure_ascii=False)})")
                continue
            n_before = len(target.tool_calls())
            reply = target.send(text)
            if show_tools:
                for tc in target.tool_calls()[n_before:]:
                    print(f"  [tool] {tc.name}({json.dumps(tc.arguments, ensure_ascii=False)})")
            print(f"agent: {reply}")
    except (EOFError, KeyboardInterrupt):
        print()
    finally:
        _save(target)


def _save(target: BlackBoxAgent) -> None:
    if len(target.trace) <= 1:
        return
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / f"chat_{target.config.name}_{datetime.now():%Y%m%d_%H%M%S}.json"
    path.write_text(
        json.dumps(
            {
                "config": target.config.name,
                "llm": target.config.agent_llm,
                "cost": target.cost(),
                "trace": [m.model_dump(mode="json", exclude_none=True) for m in target.trace],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f"saved {path}")


if __name__ == "__main__":
    app()
