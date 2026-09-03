from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def prepare(paths: list[str]) -> None:
    for path in paths:
        if Path(path).exists():
            run_git(["add", path])


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage generated skills for publishing on the current branch.")
    parser.add_argument("--path", action="append", default=["generated-skills", "published-skills.md"])
    args = parser.parse_args()
    prepare(args.path)


if __name__ == "__main__":
    main()
