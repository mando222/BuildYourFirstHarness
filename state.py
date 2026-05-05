"""
Step 4 — External State: Solving the Context Window Problem

THE PROBLEM:
If you track all task progress inside the conversation, a 20-task job means
the model's context grows with every task result. By task 15 it's slow,
expensive, and loses track of earlier decisions.

THE SOLUTION:
Store the full task list in state.json. Each agent call only sees the current
task — not the history of everything before it. The orchestrator injects
exactly what's needed, nothing more.

BONUS — crash recovery for free:
Each task is marked DONE immediately after completion and saved to disk.
If the harness is interrupted, re-running it skips all DONE tasks and
picks up from the next PLANNED one.

This is the "Kanban board" pattern from the presentation:
  PLANNED → (agent runs) → DONE
"""

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path


class Status(str, Enum):
    PLANNED = "planned"
    DONE = "done"


@dataclass
class DocTask:
    name: str       # function or class name
    item_type: str  # "function" or "class"
    line: int
    status: Status = Status.PLANNED


@dataclass
class HarnessState:
    target_file: str
    tasks: list[DocTask] = field(default_factory=list)
    report: str = ""


class StateManager:
    def __init__(self, path: str = "state.json"):
        self._path = Path(path)

    def load(self) -> HarnessState:
        if not self._path.exists():
            return HarnessState(target_file="")
        data = json.loads(self._path.read_text(encoding="utf-8"))
        tasks = [DocTask(**t) for t in data.pop("tasks", [])]
        return HarnessState(tasks=tasks, **data)

    def save(self, state: HarnessState) -> None:
        self._path.write_text(
            json.dumps(asdict(state), indent=2), encoding="utf-8"
        )


# ── Standalone demo ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    sm = StateManager(path="state_demo.json")

    state = HarnessState(
        target_file="samples/sample_code.py",
        tasks=[
            DocTask(name="calculate_average", item_type="function", line=5),
            DocTask(name="normalize",         item_type="function", line=11),
            DocTask(name="DataPipeline",      item_type="class",    line=25),
        ],
    )
    sm.save(state)
    print("Saved state_demo.json")

    loaded = sm.load()
    print(f"\nLoaded {len(loaded.tasks)} tasks for: {loaded.target_file}")
    for t in loaded.tasks:
        print(f"  [{t.status}] {t.item_type} {t.name} (line {t.line})")

    # Simulate completing one task
    loaded.tasks[0].status = Status.DONE
    sm.save(loaded)
    print("\nMarked first task DONE and saved.")
    print("Open state_demo.json to see the JSON structure.\n")

    import os
    os.remove("state_demo.json")
    print("(Cleaned up state_demo.json)")
