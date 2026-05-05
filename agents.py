"""
Step 3 — Agent Definitions: Separating "What" from "How"

run_agent() in client.py doesn't care which agent it's running.
It just takes system_prompt and tools.

AgentDefinition holds those two things (plus a name for logging).
Factory functions — make_analyzer(), make_documenter(), make_reviewer() —
return pre-configured definitions.

Swapping agents is as easy as swapping the definition you pass to run_agent().

KEY CONCEPT — Hostile Agents:
The reviewer's system prompt is deliberately adversarial. It assumes
documentation is incomplete and demands proof otherwise. This "hostile agent"
pattern creates genuine quality pressure: the documenter must do thorough work
or the reviewer will catch it.

Two agents with opposing mandates produce better outcomes than one agent
asked to both create and review its own work.
"""

from dataclasses import dataclass


@dataclass
class AgentDefinition:
    name: str
    system_prompt: str
    tools: list[str]


# ── Agent factories ──────────────────────────────────────────────────────────

def make_analyzer() -> AgentDefinition:
    return AgentDefinition(
        name="analyzer",
        system_prompt=(
            "You are a code analysis expert. Read the Python file provided "
            "and identify every function and class that is missing a docstring. "
            "Return ONLY a JSON array — no other text, no markdown fences. "
            'Each element must have exactly these keys: '
            '{"name": "item_name", "item_type": "function" or "class", "line": <line_number>}. '
            "If every item already has a docstring, return an empty array []."
        ),
        tools=["Read"],
    )


def make_documenter() -> AgentDefinition:
    return AgentDefinition(
        name="documenter",
        system_prompt=(
            "You are a Python documentation expert. You will be given a specific "
            "function or class name to document. Read the file, add a clear and "
            "accurate docstring to that item, then write the complete updated file "
            "back. Write the whole file — do not truncate or summarise. "
            "Keep existing docstrings unchanged. Be concise but complete."
        ),
        tools=["Read", "Write"],
    )


def make_reviewer() -> AgentDefinition:
    return AgentDefinition(
        name="reviewer",
        system_prompt=(
            "You are a hostile documentation reviewer. Your job is to find gaps. "
            "Read the Python file and verify that EVERY function and class has a "
            "proper docstring — not just a comment, an actual docstring (triple quotes). "
            "Assume documentation is incomplete until proven otherwise. "
            "If any item is missing a docstring, respond with:\n"
            "  NEEDS_CHANGES\n"
            "  - <item_name>: <reason>\n"
            "Only respond with the single word APPROVED (nothing else) if every "
            "function and class genuinely has a complete docstring."
        ),
        tools=["Read"],
    )


# ── Standalone demo ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    for agent in [make_analyzer(), make_documenter(), make_reviewer()]:
        print(f"{'─' * 60}")
        print(f"Agent  : {agent.name}")
        print(f"Tools  : {agent.tools}")
        print(f"Prompt : {agent.system_prompt[:120]}...")
        print()
