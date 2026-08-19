"""Terminal-Bench installed-agent adapter for `omp` (oh-my-pi).

Modeled directly on the two closest shipped adapters in the installed
`terminal_bench` package (see the class docstrings on each upstream file for
exact paths — reproduced here since this file has no network access to link
to them):

- terminal_bench/agents/installed_agents/codex/codex_agent.py   (CodexAgent)
- terminal_bench/agents/installed_agents/claude_code/claude_code_agent.py
  (ClaudeCodeAgent)

Both subclass `AbstractInstalledAgent`
(terminal_bench/agents/installed_agents/abstract_installed_agent.py), which
installs an agent CLI inside the task's Docker container via a Jinja2 setup
script, exports env vars into the container shell, then runs the agent
non-interactively with the task instruction. `omp` fits that shape exactly:
it is a CLI, not one of the externally-driven agents that need
`terminal_bench.terminal.tmux_session` control from outside the container.

This class is NOT registered in `AgentFactory.AGENT_NAME_TO_CLASS` (that
dict lives in the installed package, not this repo). Terminal-Bench supports
exactly this case via `--agent-import-path`, resolved by
`AgentFactory.get_agent_from_import_path` (agent_factory.py:64-79), which
does `importlib.import_module("bench.terminal_bench.omp_agent")` then
`getattr(module, "OmpAgent")`. Invoke it as:

    tb run --agent-import-path bench.terminal_bench.omp_agent:OmpAgent ...

run.py sets PYTHONPATH to the repo root before shelling out to `tb`, so the
`bench` package resolves the same way it does for every other module in this
repo (no separate packaging, no console-script install for `omp_agent`).
"""

from __future__ import annotations

import base64
import os
import shlex
from pathlib import Path

from terminal_bench.agents.installed_agents.abstract_installed_agent import (
    AbstractInstalledAgent,
)
from terminal_bench.terminal.models import TerminalCommand

from bench.arms.arms import arm_prompt

DEFAULT_MODEL = "openrouter/deepseek/deepseek-v4-flash-0731"
DEFAULT_THINKING = "max"
DEFAULT_ARM = "none"

# Path inside the task container where the rendered system-prompt addendum
# is written before `omp` reads it via --append-system-prompt.
CONTAINER_SYSTEM_PROMPT_PATH = "/installed-agent/append-system-prompt.txt"


class OmpAgent(AbstractInstalledAgent):
    @staticmethod
    def name() -> str:
        return "omp"

    def __init__(self, model_name: str | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model_name = model_name or os.environ.get(
            "DEEP_FABLE_MODEL", DEFAULT_MODEL
        )
        self._thinking = os.environ.get("DEEP_FABLE_THINKING", DEFAULT_THINKING)
        self._arm = os.environ.get("DEEP_FABLE_ARM", DEFAULT_ARM)
        self._version = kwargs.get("version", "latest")
        # Resolved at construction time (per assignment contract), not at
        # command-build time, so a bad arm name fails fast before any
        # container work starts.
        self._system_prompt_addendum = arm_prompt(self._arm)

    @property
    def _env(self) -> dict[str, str]:
        return {
            "OPENROUTER_API_KEY": os.environ["OPENROUTER_API_KEY"],
            "DEEP_FABLE_SYSTEM_PROMPT_B64": base64.b64encode(
                self._system_prompt_addendum.encode("utf-8")
            ).decode("ascii"),
        }

    @property
    def _install_agent_script_path(self) -> Path:
        return self._get_templated_script_path("omp-setup.sh.j2")

    def _run_agent_commands(self, instruction: str) -> list[TerminalCommand]:
        escaped_instruction = shlex.quote(instruction)
        write_prompt_file = (
            f'mkdir -p "$(dirname {CONTAINER_SYSTEM_PROMPT_PATH})" && '
            f'echo "$DEEP_FABLE_SYSTEM_PROMPT_B64" | base64 -d '
            f"> {CONTAINER_SYSTEM_PROMPT_PATH}"
        )
        omp_command = (
            f"omp --model {shlex.quote(self._model_name)} "
            f"--thinking {shlex.quote(self._thinking)} "
            f"--append-system-prompt {CONTAINER_SYSTEM_PROMPT_PATH} "
            f"--no-session --auto-approve --print {escaped_instruction}"
        )
        return [
            TerminalCommand(
                command=write_prompt_file,
                min_timeout_sec=0.0,
                max_timeout_sec=30.0,
                block=True,
                append_enter=True,
            ),
            TerminalCommand(
                command=omp_command,
                min_timeout_sec=0.0,
                max_timeout_sec=float("inf"),
                block=True,
                append_enter=True,
            ),
        ]
