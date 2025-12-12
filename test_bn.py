#!/usr/bin/env python3
"""Snapshot test runner for bn.py.

Parses test_snapshots.md and compares actual output against expected snapshots.

Usage:
    ./test_bn.py              # Run tests
    ./test_bn.py --update     # Update snapshots with current output
"""

import subprocess
import sys
import re
from pathlib import Path

SNAPSHOT_FILE = Path(__file__).parent / "test_snapshots.md"
BN_PY = Path(__file__).parent / "bn.py"


def parse_snapshots(content: str) -> list[tuple[str, str]]:
    """Parse markdown file into list of (command, expected_output) tuples."""
    tests = []

    # Split by ## headers
    sections = re.split(r'^## ', content, flags=re.MULTILINE)

    for section in sections[1:]:  # Skip header before first ##
        lines = section.strip().split('\n')
        if not lines:
            continue

        # First line is the command
        command = lines[0].strip()

        # Find code block
        code_start = None
        code_end = None
        for i, line in enumerate(lines):
            if line.strip() == '```':
                if code_start is None:
                    code_start = i + 1
                else:
                    code_end = i
                    break

        if code_start is not None and code_end is not None:
            expected = '\n'.join(lines[code_start:code_end])
            tests.append((command, expected))

    return tests


def run_command(command: str) -> str:
    """Run bn.py with the given arguments and return output."""
    import shlex
    try:
        args = shlex.split(command)
    except ValueError:
        args = command.split()

    try:
        result = subprocess.run(
            [sys.executable, str(BN_PY)] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.rstrip('\n') if result.returncode == 0 else result.stderr.rstrip('\n')
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {e}"


def run_tests() -> tuple[int, int, list[tuple[str, str, str]]]:
    """Run all tests and return (passed, failed, failures)."""
    content = SNAPSHOT_FILE.read_text()
    tests = parse_snapshots(content)

    passed = 0
    failed = 0
    failures = []

    for command, expected in tests:
        actual = run_command(command)

        if actual == expected:
            print(f"✓ {command}")
            passed += 1
        else:
            print(f"✗ {command}")
            failed += 1
            failures.append((command, expected, actual))

    return passed, failed, failures


def update_snapshots():
    """Update snapshot file with current output."""
    content = SNAPSHOT_FILE.read_text()
    tests = parse_snapshots(content)

    new_content = "# bn.py Snapshot Tests\n\nExpected output from running bn.py against test_binary.\n"

    for command, _ in tests:
        actual = run_command(command)
        print(f"Updating: {command}")
        new_content += f"\n## {command}\n\n```\n{actual}\n```\n"

    SNAPSHOT_FILE.write_text(new_content)
    print(f"\nUpdated {len(tests)} snapshots in {SNAPSHOT_FILE}")


def main():
    if "--update" in sys.argv:
        update_snapshots()
        return

    print(f"Running snapshot tests from {SNAPSHOT_FILE}\n")

    passed, failed, failures = run_tests()

    print(f"\n{'='*50}")
    print(f"Passed: {passed}, Failed: {failed}")

    if failures:
        print(f"\n{'='*50}")
        print("FAILURES:\n")
        for command, expected, actual in failures:
            print(f"## {command}")
            print(f"\nExpected:\n{expected}")
            print(f"\nActual:\n{actual}")
            print("-" * 40)
        sys.exit(1)


if __name__ == "__main__":
    main()
