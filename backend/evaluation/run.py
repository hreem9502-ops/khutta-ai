"""Command-line evaluation report.

Usage (from ``backend/``):

    python -m evaluation.run          # rule-based reader and advisor only
    python -m evaluation.run --ai     # also use Gemini (needs GEMINI_API_KEY)

Exits with status 1 if any recommendation breaks a hard rule.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from evaluation.cases import CASES_DIRECTORY, load_cases
from evaluation.harness import CaseResult, Harness


def _mark(value: bool | None) -> str:
    return "-" if value is None else ("ok" if value else "WRONG")


def print_report(results: list[CaseResult]) -> None:
    header = f"{'case':<28} {'reader':<6} {'read P/R':<11} {'gpa':<6} {'advisor':<7} {'hours':<7} {'agree P/R':<11} violations"
    print(header)
    print("-" * len(header))
    for result in results:
        reading = f"{result.reading.precision:.2f}/{result.reading.recall:.2f}"
        agreement = (
            f"{result.agreement.precision:.2f}/{result.agreement.recall:.2f}" if result.agreement else "-"
        )
        print(
            f"{result.case.name:<28} {result.reader:<6} {reading:<11} {_mark(result.reading.gpa_correct):<6} "
            f"{result.source:<7} {f'{result.total_hours}/{result.max_hours}':<7} {agreement:<11} "
            f"{len(result.violations)}"
        )
        for violation in result.violations:
            print(f"    ! {violation}")

    count = len(results)
    correct = sum(r.reading.correct for r in results)
    predicted = sum(r.reading.predicted for r in results)
    expected = sum(r.reading.expected for r in results)
    violations = sum(len(r.violations) for r in results)
    verified = [r for r in results if r.agreement]

    print()
    print(f"Cases: {count}")
    print(f"Transcript reading: precision {correct / max(predicted, 1):.2%}, recall {correct / max(expected, 1):.2%}")
    print(f"Hard-rule violations: {violations} (in {sum(1 for r in results if r.violations)} cases)")
    if verified:
        overlap = sum(r.agreement.overlap for r in verified)
        advisor = sum(r.agreement.advisor for r in verified)
        print(f"Agreement with advisors: {overlap / max(advisor, 1):.2%} of their picks ({len(verified)} cases)")
    else:
        print("Agreement with advisors: no cases with advisor_choice yet")


async def _run(directory: Path, use_ai: bool) -> list[CaseResult]:
    harness = Harness.create(use_ai=use_ai)
    return [await harness.evaluate(case) for case in load_cases(directory)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ai", action="store_true", help="use Gemini for reading fallback and advice")
    parser.add_argument("--cases", type=Path, default=CASES_DIRECTORY, help="directory of case JSON files")
    args = parser.parse_args()

    results = asyncio.run(_run(args.cases, args.ai))
    print_report(results)
    sys.exit(1 if any(result.violations for result in results) else 0)


if __name__ == "__main__":
    main()
