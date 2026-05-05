"""
Step 1 — The Minimal Agentic Loop

This is the heart of every agent harness. The loop is simple:
  1. Send a message to the model
  2. Get a response
  3. If the model wants to use a tool, execute it and loop back
  4. If not, return the text

In this step we have NO tools yet — the model can only think and respond.
Tools are added in Step 2.
"""

import asyncio

import anthropic

from config import settings


async def run_agent(
    system_prompt: str,
    task_prompt: str,
    tools: list[str] | None = None,
    cwd: str = ".",
) -> str:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    messages: list[dict] = [{"role": "user", "content": task_prompt}]
    collected_text: list[str] = []

    while True:
        response = await client.messages.create(
            model=settings.model,
            max_tokens=settings.max_tokens,
            system=system_prompt,
            messages=messages,
            tools=anthropic.NOT_GIVEN,  # no tools yet — added in step-2
        )

        for block in response.content:
            if block.type == "text":
                collected_text.append(block.text)

        # The loop has exactly ONE exit condition: the model stopped requesting tools.
        if response.stop_reason != "tool_use":
            break

    return "\n".join(collected_text)


if __name__ == "__main__":
    async def demo() -> None:
        # ── Exercise ──────────────────────────────────────────────────────────
        # Fill in the two strings below, then run:  python client.py
        #
        # system_prompt: tells the model who it is and how to behave.
        #   Try: "You are a helpful assistant. Be concise."
        #
        # task_prompt: the actual question or instruction.
        #   Try: "In one sentence, what is an 'agentic loop' in AI?"
        #
        # When you're done, checkout step-2 to see the answer and the next concept.
        # ─────────────────────────────────────────────────────────────────────

        system_prompt = ""   # ← your system prompt here
        task_prompt   = ""   # ← your task prompt here

        if not system_prompt or not task_prompt:
            print("Fill in system_prompt and task_prompt in client.py, then re-run.")
            return

        print("Running a single agent call (no tools)...\n")
        result = await run_agent(system_prompt=system_prompt, task_prompt=task_prompt)
        print("Agent response:")
        print(result)

    asyncio.run(demo())
