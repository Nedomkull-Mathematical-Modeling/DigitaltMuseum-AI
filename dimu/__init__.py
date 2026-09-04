"""Transparent client for the DigitaltMuseum public API."""

from .client import API_URL, DimuClient
from .models import (
    ArtifactFormat,
    ArtifactRequest,
    ArtifactType,
    Collection,
    CollectionsRequest,
    Country,
    FacetField,
    MatchMode,
    Occurrence,
    SearchField,
    SearchMode,
    SearchRequest,
    SearchTerm,
    SortOrder,
    StoredField,
)

__all__ = [
    "API_URL",
    "ArtifactFormat",
    "ArtifactRequest",
    "ArtifactType",
    "Collection",
    "CollectionsRequest",
    "Country",
    "DimuClient",
    "FacetField",
    "MatchMode",
    "Occurrence",
    "SearchField",
    "SearchMode",
    "SearchRequest",
    "SearchTerm",
    "SortOrder",
    "StoredField",
    "main",
]


def main(argv: list[str] | None = None) -> int:
    """Run the command-line client."""
    from .cli import main as cli_main

    return cli_main(argv)
