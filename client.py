"""
Step 2 — The Agentic Loop With Tools

In step 1 the loop always exited immediately (no tools).
Now the model can request tools, we execute them, and the loop continues
until stop_reason is no longer "tool_use".

The key change is the tool execution block inside the while loop.
"""

import asyncio

import anthropic

from config import settings
from tools import build_tool_list, execute_tool


async def run_agent(
    system_prompt: str,
    task_prompt: str,
    tools: list[str] | None = None,
    cwd: str = ".",
) -> str:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    tool_defs = build_tool_list(tools or [])
    messages: list[dict] = [{"role": "user", "content": task_prompt}]
    collected_text: list[str] = []

    while True:
        response = await client.messages.create(
            model=settings.model,
            max_tokens=settings.max_tokens,
            system=system_prompt,
            messages=messages,
            # Pass tools only when the agent has some — empty list behaves
            # differently from NOT_GIVEN on some models.
            tools=tool_defs if tool_defs else anthropic.NOT_GIVEN,
        )

        for block in response.content:
            if block.type == "text":
                collected_text.append(block.text)

        # THE only exit condition — model is done with tools.
        if response.stop_reason != "tool_use":
            break

        # ── Execute every tool the model requested this turn ─────────────
        tool_results: list[dict] = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            output, is_error = await execute_tool(block.name, dict(block.input), cwd)
            print(f"    [{block.name}] {str(block.input)[:70]}")
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                    "is_error": is_error,
                }
            )

        # Append the model's turn (with tool_use blocks) then the results.
        # The model sees these on the next iteration and decides what to do next.
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return "\n".join(collected_text)


if __name__ == "__main__":
    async def demo() -> None:
        print("Running an agent with the Read tool...\n")
        result = await run_agent(
            system_prompt=(
                "You are a helpful assistant. When asked about a file, "
                "read it first, then answer."
            ),
            task_prompt=(
                "Read samples/sample_code.py and tell me in two sentences "
                "what the DataPipeline class does."
            ),
            tools=["Read"],
            cwd=".",
        )
        print("\nAgent response:")
        print(result)

    asyncio.run(demo())
