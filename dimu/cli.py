"""Command-line interface using the public client and request model."""

from __future__ import annotations

import argparse
import json
import sys
from xml.etree.ElementTree import ParseError

import httpx
from pydantic import ValidationError

from .client import DimuClient
from .models import ArtifactFormat, Country, SearchRequest


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query the DigitaltMuseum API")
    commands = parser.add_subparsers(dest="command", required=True)

    owner_parser = commands.add_parser("owners", help="list museums/collections")
    owner_parser.add_argument("--country", default="se", choices=("se", "no"))

    search_parser = commands.add_parser("search", help="search published records")
    search_parser.add_argument("query")
    search_parser.add_argument("--owner", action="append", default=[], help="owner code; may be repeated")
    search_parser.add_argument("--rows", type=_positive_int, default=10)
    search_parser.add_argument("--pictures", action="store_true")

    artifact_parser = commands.add_parser("artifact", help="fetch one full record")
    artifact_parser.add_argument("unique_id")
    artifact_parser.add_argument("--format", default="simple_json", choices=[item.value for item in ArtifactFormat])
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    args = _parser().parse_args(argv)
    try:
        with DimuClient() as client:
            if args.command == "owners":
                result = [item.model_dump(mode="json") for item in client.collections(Country(args.country))]
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
            if args.command == "search":
                response = client.search(
                    SearchRequest(
                        query=args.query,
                        collection_ids=args.owner,
                        limit=args.rows,
                        has_pictures=True if args.pictures else None,
                    )
                )
            else:
                response = client.artifact(args.unique_id, args.format)
            response.raise_for_status()
            sys.stdout.buffer.write(response.content)
            if not response.content.endswith(b"\n"):
                sys.stdout.buffer.write(b"\n")
            return 0
    except (httpx.HTTPError, ValidationError, ValueError, ParseError) as error:
        print(f"DigitaltMuseum request failed: {error}", file=sys.stderr)
        return 1
