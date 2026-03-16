#!/usr/bin/env python3
"""Format flashcard pairs into a tab-separated file for Quizlet import.

Reads flashcard pairs from stdin as JSON and writes a properly
tab-separated text file. This guarantees literal tab characters
between front and back, which LLM chat output cannot reliably do.

Usage:
    echo '[["front1","back1"],["front2","back2"]]' | python format_flashcards.py OUTPUT_PATH

Input: JSON array of [front, back] pairs on stdin
Output: Tab-separated file at OUTPUT_PATH, one card per line
"""

import json
import sys


def main():
    if len(sys.argv) != 2:
        print("Usage: echo JSON | python format_flashcards.py OUTPUT_PATH", file=sys.stderr)
        sys.exit(1)

    output_path = sys.argv[1]

    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list) or not all(
        isinstance(pair, list) and len(pair) == 2 for pair in data
    ):
        print("Input must be a JSON array of [front, back] pairs", file=sys.stderr)
        sys.exit(1)

    lines = []
    for front, back in data:
        front = str(front).replace("\t", " ").replace("\n", " ").strip()
        back = str(back).replace("\t", " ").replace("\n", " ").strip()
        lines.append(f"{front}\t{back}")

    content = "\n".join(lines) + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Wrote {len(lines)} flashcards to {output_path}")


if __name__ == "__main__":
    main()
