"""
Step 5 — Entry Point

Run the full harness:
  python3 main.py samples/sample_code.py

Or via make:
  make run
"""

import asyncio
import sys

from orchestrator import HarnessOrchestrator


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <path/to/file.py>")
        sys.exit(1)

    target = sys.argv[1]
    print(f"Code Documenter Harness")
    print(f"Target : {target}")
    print(f"Output : state.json  report.md  (updated target file)")
    asyncio.run(HarnessOrchestrator(target).run())


if __name__ == "__main__":
    main()
