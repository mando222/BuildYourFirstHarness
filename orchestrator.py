"""
Step 5 — The Orchestrator: Tying It All Together

HarnessOrchestrator coordinates three agents across three phases:

  Phase 1 — Analyze:   Analyzer reads the file → saves task list to state.json
  Phase 2 — Document:  Documenter runs once per task → updates state.json after each
  Phase 3 — Review:    Hostile Reviewer reads the file → one fix pass if NEEDS_CHANGES

KEY CONCEPTS demonstrated here:

  Workload isolation:
    Each agent only sees its current task. The Documenter documenting
    `normalize()` has no idea what happened with `calculate_average()`.
    Context stays small and focused.

  Crash recovery (free because of state.py):
    _phase_document() skips tasks already marked DONE. Interrupt the
    harness mid-run and re-run — it picks up exactly where it left off.

  Hostile review loop:
    The Reviewer assumes documentation is incomplete. If it returns
    NEEDS_CHANGES, we run one more Documenter pass. Max one cycle —
    the guard prevents an infinite retry loop.
"""

import asyncio
import json
from pathlib import Path

from agents import make_analyzer, make_documenter, make_reviewer
from client import run_agent
from state import DocTask, HarnessState, StateManager, Status


class HarnessOrchestrator:
    def __init__(self, target_file: str, state_path: str = "state.json"):
        self.target = Path(target_file).resolve()
        self.cwd = str(self.target.parent)
        self.sm = StateManager(path=state_path)

    async def run(self) -> None:
        await self._phase_analyze()
        await self._phase_document()
        await self._phase_review()
        self._write_report()
        print("\nDone. See report.md and state.json.")

    # ── Phase 1: Analyze ────────────────────────────────────────────────────

    async def _phase_analyze(self) -> None:
        print("\n[Phase 1/3] Analyzing code...")
        agent = make_analyzer()
        result = await run_agent(
            system_prompt=agent.system_prompt,
            task_prompt=f"Analyze this file for undocumented items: {self.target}",
            tools=agent.tools,
            cwd=self.cwd,
        )
        try:
            items = json.loads(result.strip())
        except json.JSONDecodeError:
            cleaned = result.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            items = json.loads(cleaned)

        state = HarnessState(
            target_file=str(self.target),
            tasks=[DocTask(**item) for item in items],
        )
        self.sm.save(state)
        print(f"  Found {len(items)} items to document.")

    # ── Phase 2: Document each task ─────────────────────────────────────────

    async def _phase_document(self) -> None:
        print("\n[Phase 2/3] Documenting...")
        state = self.sm.load()

        for task in state.tasks:
            # ── Exercise ──────────────────────────────────────────────────────
            # Add two things to this loop — they implement crash recovery and
            # workload isolation:
            #
            # 1. SKIP already-done tasks:
            #       if task.status == Status.DONE:
            #           print(f"  Skipping {task.name} (already done)")
            #           continue
            #
            # 2. After the agent call below, mark the task done and save:
            #       task.status = Status.DONE
            #       self.sm.save(state)
            #
            # To verify: run `python main.py samples/sample_code.py`, press Ctrl-C
            # partway through Phase 2, then run it again — completed tasks should be skipped.
            # ─────────────────────────────────────────────────────────────────

            print(f"  Documenting: {task.name} ({task.item_type}, line {task.line})")
            agent = make_documenter()
            await run_agent(
                system_prompt=agent.system_prompt,
                task_prompt=(
                    f"Add a docstring to the {task.item_type} '{task.name}' "
                    f"(around line {task.line}) in the file: {self.target}"
                ),
                tools=agent.tools,
                cwd=self.cwd,
            )

    # ── Phase 3: Hostile review ─────────────────────────────────────────────

    async def _phase_review(self) -> None:
        print("\n[Phase 3/3] Hostile review...")
        agent = make_reviewer()
        result = await run_agent(
            system_prompt=agent.system_prompt,
            task_prompt=f"Review the documentation in: {self.target}",
            tools=agent.tools,
            cwd=self.cwd,
        )

        if "NEEDS_CHANGES" in result:
            print("  Reviewer found gaps — running one fix pass...")
            fixer = make_documenter()
            await run_agent(
                system_prompt=fixer.system_prompt,
                task_prompt=(
                    f"The reviewer found these documentation gaps. Fix them all in "
                    f"{self.target}:\n\n{result}"
                ),
                tools=fixer.tools,
                cwd=self.cwd,
            )
            print("  Fix pass complete.")
        else:
            print("  Reviewer: APPROVED")

    # ── Write report ────────────────────────────────────────────────────────

    def _write_report(self) -> None:
        state = self.sm.load()
        done = [t for t in state.tasks if t.status == Status.DONE]
        lines = [
            "# Documentation Report\n",
            f"**File**: `{state.target_file}`  ",
            f"**Items documented**: {len(done)}\n",
            "## Documented Items\n",
        ]
        for t in done:
            lines.append(f"- `{t.name}` ({t.item_type}, line {t.line})")
        state.report = "\n".join(lines)
        self.sm.save(state)
        Path("report.md").write_text(state.report, encoding="utf-8")
        print("  report.md written.")


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "samples/sample_code.py"
    asyncio.run(HarnessOrchestrator(target).run())
