# 🤖 Build a Multi-Agent Harness from Scratch

A hands-on, 60-minute workshop that takes you from "what even is an agent?" to a **fully working multi-agent harness** — one you built yourself, line by line.

By the end you'll have a **Code Documenter Harness**: a team of AI agents that reads a Python file, documents every function and class, runs a hostile review pass, and writes a report. More importantly, you'll understand *why* it's built the way it is.

---

## What You'll Build

```
Your Python file
      │
      ▼
 [Analyzer] ──► state.json (task list)
      │
      ▼
 [Documenter] × N ──► writes docstrings back to the file
      │
      ▼
 [Hostile Reviewer] ──► APPROVED  (or triggers one fix pass)
      │
      ▼
   report.md
```

Five focused files. Seven concepts. One working harness.

---

## Why Harnesses? The Problem With Bare LLMs

Before writing any code, it helps to understand *why* a harness is needed at all.

A language model is a **decoder** — it predicts the next token based on everything it has seen so far. For short, deterministic tasks that works fine. But for complex, multi-step work, three problems compound:

**1. Entropy accumulates.** Every token is a probability distribution, not a fact lookup. Small uncertainties stack up — the model drifts from the original intent like a compass that's slightly off.

**2. The context window is a liability.** If you store all progress inside the conversation, long tasks eventually overflow. The model loses track of what it already decided.

**3. No real self-correction.** A single model asked to both write *and* review its own work is biased toward agreeing with itself. It likes to agree.

**The harness solution:**

| Problem | Solution |
|---------|----------|
| Entropy / drift | Break work into focused sub-tasks — each agent only sees what it needs |
| Context overflow | Store progress externally (a JSON file, not the context window) |
| No self-correction | Use hostile agents — a reviewer whose job is to find problems |

```
Bare LLM:   Task ──→ [Model] ──→ Output (may drift)

Harness:    Task ──→ [Analyzer] ──→ state.json
                                        ↓
                              [Documenter × N] ──→ state.json (updated)
                                        ↓
                            [Hostile Reviewer] ──→ APPROVED / NEEDS_CHANGES
                                        ↓
                                    report.md
```

---

## Concepts Covered

| Step | File(s) | What You Learn |
|------|---------|----------------|
| 1 | `config.py`, `client.py` | The agentic loop — the `while True` that drives everything |
| 2 | `tools.py` | Tool schemas, `stop_reason == "tool_use"`, the dispatcher |
| 3 | `agents.py` | Separating *what* an agent is from *how* it runs; hostile agents |
| 4 | `state.py` | Why the context window is a liability and how to solve it |
| 5 | `orchestrator.py` | Pipelines, workload isolation, crash recovery |

---

## Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)
- Basic Python comfort — you don't need to know `async/await` upfront, it's explained as you go

---

## Setup

```bash
# 1. Clone
git clone https://github.com/mando222/BuildYourFirstHarness
cd BuildYourFirstHarness

# 2. Virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. API key
cp .env.example .env
# Open .env and set:
#   ANTHROPIC_API_KEY=sk-ant-...
```

> **Tip:** Your `venv/` folder is gitignored — it stays intact when you switch between steps, so you only need to install once. Once the venv is active, use `python` (not `python3`) — the venv wires it up for you.

---

## How the Workshop Works

Each step is a **git tag**. Check out a tag to get the code at exactly that point, read the new file(s), complete the exercise, then move on.

```bash
git checkout -f step-1   # start here
git checkout -f step-2   # adds tools
git checkout -f step-3   # adds agent definitions
git checkout -f step-4   # adds external state
git checkout -f step-5   # the full working harness
```

**Moving between steps after editing files:**  
Each step has an exercise that modifies a file. The `-f` flag handles this — it discards local changes and switches cleanly:

```bash
git checkout -f step-2   # move on, local changes discarded
```

Want to keep your exercise work before moving on? Stash it first:

```bash
git stash && git checkout -f step-2
```

Fell behind or something broke? Jump straight to any step:

```bash
git checkout -f step-3   # instantly back on track
```

---

## Step 1 — The Minimal Agentic Loop `(~10 min)`

```bash
git checkout -f step-1
```

**New files:** `config.py`, `client.py`, `samples/sample_code.py`

The agentic loop is the engine of every harness. It's simpler than it sounds:

```python
while True:
    response = call_the_model(messages)
    collect_text(response)
    if response.stop_reason != "tool_use":
        break                        # ← the only exit condition
    # (tools are added in step 2)
```

### 1a. Configuration (`config.py`)

Open `config.py`. Two things to notice:

- `load_dotenv(override=True)` — reads `.env` and sets `os.environ`, with `override=True` so the file always wins over any empty shell variables
- `@lru_cache` on `get_settings()` — only one `Settings` instance is ever created; every file that does `from config import settings` gets the same object

```bash
python config.py
```

You should see your model name, token limit, and a preview of your API key. If the key shows `(not set)`, double-check your `.env` file.

### 1b. The Agentic Loop (`client.py`)

Open `client.py`. The `run_agent` function is the core of every agent harness. Right now it has **no tools** — the model can only think and respond. The loop's only exit condition is `stop_reason != "tool_use"`, which always fires immediately when there are no tools.

### ✏️ Exercise

Scroll to the bottom of `client.py`. You'll see the `demo()` function with two empty strings:

```python
system_prompt = ""   # ← your system prompt here
task_prompt   = ""   # ← your task prompt here
```

Fill them in. The system prompt tells the model who it is; the task prompt is your actual question. Try:

```python
system_prompt = "You are a helpful assistant. Be concise."
task_prompt   = "In one sentence, what is an 'agentic loop' in AI?"
```

Then run it:

```bash
python client.py
```

You should see a one-sentence answer come back from the model. That's the full agentic loop running — it exited immediately on the first pass because there are no tool calls yet. When you checkout step-2 your prompts will be filled in so you can compare.

### 1c. The Sample File (`samples/sample_code.py`)

Open `samples/sample_code.py`. It's a clean, working Python module — 4 functions and 1 class, all correct, none with docstrings. This is what the harness will document.

---

## Step 2 — Giving Agents Hands `(~10 min)`

```bash
git checkout -f step-2
```

**New files:** `tools.py` &nbsp;|&nbsp; **Updated:** `client.py`

A tool is two things glued together:
1. **A JSON schema** the model uses to decide when and how to call the tool
2. **A Python function** that actually runs when the model chooses it

### 2a. Tool Definitions (`tools.py`)

Open `tools.py`. There are two tools: `Read` and `Write`. Each has a JSON schema (so the model knows it exists and how to call it) and a handler in `execute_tool()` (the Python that actually runs). The `TOOLS` dict maps names to schemas:

```python
TOOLS: dict[str, dict] = {
    "Read": {
        "name": "Read",
        "description": "Read the full contents of a file.",
        "input_schema": { "type": "object", "properties": { "file_path": {...} }, ... },
    },
    "Write": { ... },
}
```

Run the demo to confirm `Read` works — no model involved yet:

```bash
python tools.py
```

You'll see the contents of `samples/sample_code.py` printed directly by the tool executor.

### ✏️ Exercise

Open `tools.py` and find the `if name == "Write":` block in `execute_tool()`. Right now it just returns an error. Implement it:

```python
if name == "Write":
    path = base / tool_input["file_path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tool_input["content"], encoding="utf-8")
    return f"Written {len(tool_input['content'])} chars to {path}", False
```

The model passes `file_path` and `content` — your job is to write the bytes to disk and report back.

### 2b. The Tool-Use Loop (`client.py`)

Open the updated `client.py`. The new addition inside the loop:

```python
# Inside the while loop, after the stop_reason check:
for block in response.content:
    if block.type == "tool_use":
        output, is_error = await execute_tool(block.name, dict(block.input), cwd)
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": output,
        })
messages.append({"role": "assistant", "content": response.content})
messages.append({"role": "user",      "content": tool_results})
# loop continues → model sees results → decides what to do next
```

The model is now in a **genuine conversation with its own tools**. Each tool result is appended as a message, and the model decides what to do next until `stop_reason == "end_turn"`.

```bash
python client.py
```

You'll see `[Read]` log lines as the agent reads the file, then a description of what it found. The loop ran multiple iterations this time. Checkout step-3 to see your Write implementation and the next concept.

---

## Step 3 — Agent Definitions & Hostile Agents `(~10 min)`

```bash
git checkout -f step-3
```

**New files:** `agents.py`

### 3a. The AgentDefinition Dataclass

`run_agent()` doesn't care which agent it's running — it just takes a system prompt and a list of tool names. `AgentDefinition` packages those up:

```python
@dataclass
class AgentDefinition:
    name: str
    system_prompt: str
    tools: list[str]
```

This separation matters: swapping agents is as easy as swapping the definition. The loop in `client.py` is unchanged — only the instructions change.

### 3b. The Hostile Reviewer

Look at `make_reviewer()`. The analyzer and documenter are fully defined — but the reviewer's `system_prompt` is empty. That's your exercise.

### ✏️ Exercise

Open `agents.py` and write the hostile reviewer's system prompt. It should:
- Tell the agent to read the file and check **every** function and class
- Assume documentation is **missing** until proven otherwise
- Respond `NEEDS_CHANGES` followed by what's missing, if anything is wrong
- Respond with only the word `APPROVED` if everything is complete

Here's one that works well:

```python
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
```

The adversarial framing is the point — two agents with opposing mandates produce better results than one agent reviewing its own work.

```bash
python agents.py
```

You'll see each agent's name, tools, and system prompt printed. Notice how different the reviewer feels — same loop, completely different personality. Checkout step-4 to see the answer and the next concept.

---

## Step 4 — External State `(~10 min)`

```bash
git checkout -f step-4
```

**New files:** `state.py`

### 4a. The Problem

Imagine the harness needs to document 20 functions. If you track all 20 inside the conversation, by function 15 the model has a huge context window full of old tool results — it slows down, costs more, and can lose track of earlier decisions.

The fix: **store state externally and inject only what's needed**.

```
BAD:  context = [task1_result, task2_result, ..., task15_result, → do task 16]
GOOD: context = [→ do task 16]    # state.json holds everything else
```

### 4b. StateManager (`state.py`)

Open `state.py`. `HarnessState` holds the target file and a list of `DocTask` objects. `StateManager.load()` is already implemented — it reads JSON from disk and reconstructs the dataclasses. The key insight is in the status enum:

```python
class Status(str, Enum):
    PLANNED = "planned"
    DONE    = "done"
```

When the orchestrator processes tasks, it skips anything already `DONE`. This means if the harness crashes mid-run, restarting it picks up exactly where it left off — crash recovery for free.

### ✏️ Exercise

`StateManager.save()` is stubbed with `pass`. Implement it:

```python
def save(self, state: HarnessState) -> None:
    self._path.write_text(
        json.dumps(asdict(state), indent=2), encoding="utf-8"
    )
```

Three parts: `asdict()` converts the dataclass to a plain dict, `json.dumps()` serializes it, `write_text()` persists it. That's the entire external state mechanism.

```bash
python state.py
```

If it works, you'll see `state_demo.json` created, the tasks listed, and then the file cleaned up. Open the JSON while it exists to see the structure — this is the harness's entire memory. Checkout step-5 to see the answer and the final pipeline.

---

## Step 5 — The Full Pipeline `(~10 min)`

```bash
git checkout -f step-5
```

**New files:** `orchestrator.py`, `main.py`, `Makefile`

### 5a. The Orchestrator (`orchestrator.py`)

Open `orchestrator.py`. The `HarnessOrchestrator` class has one method per phase:

```
run()
 ├── _phase_analyze()    Analyzer reads file → task list → state.json
 ├── _phase_document()   Documenter runs once per task → saves after each
 ├── _phase_review()     Hostile Reviewer checks everything → fix pass if needed
 └── _write_report()     writes report.md
```

### ✏️ Exercise

Find `_phase_document()`. The loop runs the documenter for each task, but it's missing the two lines that make crash recovery work. Add them:

```python
for task in state.tasks:
    # 1. Skip tasks already completed on a previous run
    if task.status == Status.DONE:
        print(f"  Skipping {task.name} (already done)")
        continue

    print(f"  Documenting: {task.name} ...")
    await run_agent(...)   # ← already there

    # 2. Persist immediately after each task
    task.status = Status.DONE
    self.sm.save(state)
```

Without these two lines the harness works — but if it crashes, it starts over from scratch. With them, it picks up exactly where it left off.

### 5b. Run It

```bash
make run
# or: python main.py samples/sample_code.py
```

Watch the three phases execute — you'll see phase labels, `[Read]`/`[Write]` tool calls per task, and a final `APPROVED` or fix-pass message from the reviewer. When it finishes, inspect:

- `samples/sample_code.py` — open it and compare to the original: every function and class now has a docstring
- `state.json` — all tasks show `"status": "done"`
- `report.md` — a summary of what was documented and the reviewer's verdict

### 5c. Test Crash Recovery

Once you've added the two exercise lines, verify they actually work:

```bash
make clean                               # reset everything to original state
python main.py samples/sample_code.py  # start the harness
# Press Ctrl-C partway through Phase 2
python main.py samples/sample_code.py  # re-run — already-done tasks are skipped
```

On the second run you'll see `Skipping <name> (already done)` for completed tasks, then it picks up where it left off. That's the crash recovery working. Without those two lines, it would document everything from scratch again.

---

## What You Built

| File | ~Lines | Role |
|------|--------|------|
| `config.py` | 40 | Single settings object loaded from `.env` |
| `tools.py` | 75 | Tool schemas + async executor |
| `client.py` | 55 | The agentic loop — one function drives everything |
| `agents.py` | 90 | Agent definitions, separated from execution |
| `state.py` | 65 | External state — crash recovery and context isolation |
| `orchestrator.py` | 105 | Three-phase pipeline |
| `main.py` | 20 | Entry point |

**Total: ~450 lines.** That's a complete multi-agent harness.

---

## Going Further

Once the harness is running, natural next steps:

- **Add a Planner agent** — a pure-reasoning agent (no tools) that decides task order and priority before the Documenter starts
- **Parallel execution** — swap the sequential `for` loop in `_phase_document()` for `asyncio.gather()` and document multiple items at once
- **AAAK Compression** — after each agent writes its output, a second LLM call summarizes it to ~1/30 the size before it's stored in `state.json`. This lets harnesses run indefinitely without growing the context window
- **See it at scale** — [`githubFixer`](https://github.com/mando222/githubFixer) applies these exact patterns to autonomously solve GitHub issues end-to-end, with rate limiting, semaphore concurrency, and context compaction

---

## Model & Cost

The harness uses `claude-sonnet-4-5-20250929` by default. A full run on the sample file typically costs **under $0.10**. You can swap to a cheaper model anytime by setting `MODEL=` in your `.env`.

---

*Built as part of the "Harnesses Supercharge Your Efforts" workshop series.*
