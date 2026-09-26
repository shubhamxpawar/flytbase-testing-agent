"""Small command-line entry point for validating configuration and locator maps."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_capabilities, load_target
from .locators import LocatorMap
from .runner import RunnerPreflightError, run_capabilities


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentic-testing")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-config")
    validate.add_argument("target", type=Path)
    validate.add_argument("capabilities", type=Path)
    inspect = commands.add_parser("locators")
    inspect.add_argument("map_path", type=Path)
    inspect.add_argument("target_id")
    inspect.add_argument("--clear", action="store_true")
    run = commands.add_parser("run")
    run.add_argument("--target", type=Path, required=True)
    run.add_argument("--capabilities", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    display = run.add_mutually_exclusive_group()
    display.add_argument("--headed", dest="headless", action="store_false", help="show Chromium (default)")
    display.add_argument("--headless", dest="headless", action="store_true", help="run Chromium without a window")
    run.add_argument(
        "--reuse-session",
        action="store_true",
        help="reuse one browser context across capabilities; intended for headed demos",
    )
    run.set_defaults(headless=False)
    args = parser.parse_args(argv)

    if args.command == "validate-config":
        target = load_target(args.target)
        capabilities = load_capabilities(args.capabilities)
        print(f"validated target={target.target_id} capabilities={len(capabilities)}")
        return 0
    if args.command == "run":
        try:
            result = run_capabilities(
                args.target,
                args.capabilities,
                args.out,
                headless=args.headless,
                reuse_session=args.reuse_session,
            )
        except RunnerPreflightError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        print(json.dumps({"run_dir": result["run_dir"], "finding_count": result["summary"]["finding_count"]}))
        return 0
    locator_map = LocatorMap(args.map_path)
    if args.clear:
        print(f"cleared={locator_map.clear_target(args.target_id)}")
        locator_map.save()
    else:
        for item in locator_map.records_for_target(args.target_id):
            print(f"{item.key.page_identity}\t{item.key.element_intent}\t{item.strategy}\t{item.value}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
