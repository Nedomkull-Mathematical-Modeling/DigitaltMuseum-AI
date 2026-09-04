"""HTTP-klient för DigitaltMuseum utan normalisering av svar."""

from __future__ import annotations

import os
import warnings
from xml.etree import ElementTree

import httpx

from .models import ArtifactFormat, ArtifactRequest, Collection, Country, SearchRequest

API_URL = "https://api.dimu.org"


class DimuClient:
    """Återanvändbar synkron klient för DigitaltMuseums publika API."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = API_URL,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("DIMU_API_KEY") or "demo"
        if self.api_key == "demo":
            warnings.warn(
                "dimu använder DigitaltMuseums demo-nyckel; sätt DIMU_API_KEY för produktion",
                RuntimeWarning,
                stacklevel=2,
            )
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            transport=transport,
            follow_redirects=True,
            headers={"User-Agent": "dimu/0.2"},
        )

    def __enter__(self) -> "DimuClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        """Stäng poolade nätverksanslutningar."""
        self._client.close()

    def _get(self, path: str, params: list[tuple[str, str]]) -> httpx.Response:
        return self._client.get(path, params=[*params, ("api.key", self.api_key)])

    def search(self, request: SearchRequest) -> httpx.Response:
        """Kör en sökning och returnera DigitaltMuseums otolkade svar."""
        return self._get("/api/solr/select", request.to_params())

    def artifact(
        self,
        unique_id: str,
        format: ArtifactFormat | str = ArtifactFormat.SIMPLE_JSON,
    ) -> httpx.Response:
        """Hämta ett fullständigt objekt och returnera det otolkade svaret."""
        request = ArtifactRequest(unique_id=unique_id, format=format)
        return self._get(
            "/api/artifact",
            [("unique_id", request.unique_id), ("mapping", request.format.value)],
        )

    def collections_raw(self, country: Country | str) -> httpx.Response:
        """Hämta den ursprungliga XML-listan över publicister för ett land."""
        return self._get("/api/owners", [("country", Country(country).value)])

    def collections(self, country: Country | str) -> list[Collection]:
        """Tolka publicistlistan till den lilla JSON-form som chatboten använder."""
        selected_country = Country(country)
        response = self.collections_raw(selected_country)
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        return [
            Collection(
                identifier=owner.findtext("identifier", ""),
                name=owner.findtext("name", ""),
                parent=owner.findtext("parent"),
                country=selected_country,
            )
            for owner in root.findall("owner")
        ]
