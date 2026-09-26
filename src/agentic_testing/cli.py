"""Small command-line entry point for validating configuration and locator maps."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_capabilities, load_target
from .locators import LocatorMap


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
    args = parser.parse_args(argv)

    if args.command == "validate-config":
        target = load_target(args.target)
        capabilities = load_capabilities(args.capabilities)
        print(f"validated target={target.target_id} capabilities={len(capabilities)}")
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
