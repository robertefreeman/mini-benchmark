from __future__ import annotations

import argparse
import sys

from .remote import build_remote_parsers, dispatch_remote_command
from .runner import build_run_scenario_parser, build_summarize_parser, dispatch_runner_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HumanEval+ benchmark harness")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_run_scenario_parser(subparsers)
    build_summarize_parser(subparsers)
    build_remote_parsers(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in {"run-scenario", "summarize-run"}:
        return dispatch_runner_command(args)
    return dispatch_remote_command(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

