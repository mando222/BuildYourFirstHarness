"""
Step 2 — Tools: Giving Agents Hands

A tool is two things:
  1. A JSON schema the model uses to decide when and how to call it
  2. A Python function that actually runs when the model chooses it

We define two tools: Read (read a file) and Write (write content to a file).
execute_tool() is the dispatcher — it receives what the model requested and does it.
"""

from pathlib import Path


# ── Tool schemas (Anthropic API format) ─────────────────────────────────────

TOOLS: dict[str, dict] = {
    "Read": {
        "name": "Read",
        "description": "Read the full contents of a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file, relative to the working directory.",
                },
            },
            "required": ["file_path"],
        },
    },
    "Write": {
        "name": "Write",
        "description": "Write content to a file, creating it if it does not exist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file, relative to the working directory.",
                },
                "content": {
                    "type": "string",
                    "description": "The full content to write to the file.",
                },
            },
            "required": ["file_path", "content"],
        },
    },
}


def build_tool_list(names: list[str]) -> list[dict]:
    """Return API-ready tool dicts for the given tool names."""
    return [TOOLS[n] for n in names if n in TOOLS]


# ── Tool executor ────────────────────────────────────────────────────────────

async def execute_tool(
    name: str, tool_input: dict, cwd: str
) -> tuple[str, bool]:
    """
    Run a tool and return (output_text, is_error).
    Called by the agent loop whenever the model emits a tool_use block.
    """
    base = Path(cwd)

    if name == "Read":
        path = base / tool_input["file_path"]
        try:
            return path.read_text(encoding="utf-8"), False
        except FileNotFoundError:
            return f"File not found: {path}", True

    if name == "Write":
        # ── Exercise ──────────────────────────────────────────────────────────
        # Implement the Write tool. The model passes:
        #   tool_input["file_path"]  — where to write (relative to `base`)
        #   tool_input["content"]    — the full text to write
        #
        # Your implementation should:
        #   1. Build the full path:   path = base / tool_input["file_path"]
        #   2. Create parent dirs:    path.parent.mkdir(parents=True, exist_ok=True)
        #   3. Write the content:     path.write_text(tool_input["content"], encoding="utf-8")
        #   4. Return a success message and False (not an error):
        #              return f"Written ... chars to {path}", False
        #
        # When you're done, run:  python tools.py
        # Checkout step-3 to see the answer and the next concept.
        # ─────────────────────────────────────────────────────────────────────
        return "Write not yet implemented — complete the exercise above.", True

    return f"Unknown tool: {name}", True


# ── Standalone demo ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    async def demo() -> None:
        print("Reading samples/sample_code.py via the Read tool...\n")
        content, is_error = await execute_tool(
            "Read", {"file_path": "samples/sample_code.py"}, "."
        )
        if is_error:
            print(f"Error: {content}")
        else:
            print(content)

    asyncio.run(demo())
