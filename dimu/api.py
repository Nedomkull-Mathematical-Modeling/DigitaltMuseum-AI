"""FastAPI-proxy som validerar frågor och bevarar DigitaltMuseums svar."""

from __future__ import annotations

import copy
import hmac
import os
from contextlib import asynccontextmanager
from typing import Annotated, Any, Callable
from xml.etree import ElementTree

import httpx
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse, Response

from .client import DimuClient
from .models import (
    ArtifactFormat,
    ArtifactRequest,
    Collection,
    CollectionsRequest,
    Country,
    SearchRequest,
)


def _strict_schema(model: type[SearchRequest] | type[ArtifactRequest] | type[CollectionsRequest]) -> dict[str, Any]:
    """Konvertera ett Pydantic-schema till OpenAI:s strict-format."""
    schema = copy.deepcopy(model.model_json_schema())

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            value.pop("default", None)
            if isinstance(value.get("format"), str):
                value.pop("format")
            properties = value.get("properties")
            if isinstance(properties, dict):
                value["additionalProperties"] = False
                value["required"] = list(properties)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(schema)
    return schema


def openai_tools() -> list[dict[str, Any]]:
    """Returnera verktygsdefinitioner för OpenAI Responses API."""
    return [
        {
            "type": "function",
            "name": "search_digitaltmuseum",
            "description": (
                "Sök oförändrade poster i DigitaltMuseum. Använd strukturerade fält i första hand; "
                "raw_query och raw_filter_queries finns när exakt Solr-syntax behövs. Svaret är "
                "DigitaltMuseums fullständiga råa JSON och ska inte antas ha en förenklad form."
            ),
            "parameters": _strict_schema(SearchRequest),
            "strict": True,
        },
        {
            "type": "function",
            "name": "get_digitaltmuseum_artifact",
            "description": (
                "Hämta den fullständiga, oförändrade posten för ett unique_id eller uuid från en sökträff. "
                "Använd simple_json för chatbotläsning och ABM eller ESE endast när originalformatet behövs."
            ),
            "parameters": _strict_schema(ArtifactRequest),
            "strict": True,
        },
        {
            "type": "function",
            "name": "list_digitaltmuseum_collections",
            "description": (
                "Lista svenska och/eller norska museer och samlingar samt deras identifierare, så att en "
                "senare sökning kan begränsas med collection_ids."
            ),
            "parameters": _strict_schema(CollectionsRequest),
            "strict": True,
        },
    ]


def _upstream(call: Callable[[], httpx.Response]) -> httpx.Response:
    try:
        response = call()
    except httpx.TimeoutException as error:
        raise HTTPException(status_code=504, detail="DigitaltMuseum svarade inte inom tidsgränsen.") from error
    except httpx.RequestError as error:
        raise HTTPException(status_code=502, detail="Det gick inte att kontakta DigitaltMuseum.") from error
    if not response.is_success:
        raise HTTPException(
            status_code=502,
            detail=f"DigitaltMuseum svarade med HTTP {response.status_code}.",
        )
    return response


def _verbatim(response: httpx.Response) -> Response:
    headers = {}
    if content_type := response.headers.get("content-type"):
        headers["content-type"] = content_type
    return Response(content=response.content, status_code=response.status_code, headers=headers)


def create_app(
    *,
    client: DimuClient | None = None,
    api_key: str | None = None,
    service_token: str | None = None,
) -> FastAPI:
    """Skapa API:t; miljökonfigurationen kontrolleras vid start."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        token = service_token or os.getenv("DIMU_SERVICE_TOKEN")
        if not token:
            raise RuntimeError("DIMU_SERVICE_TOKEN krävs")

        app.state.service_token = token
        app.state.dimu = client or DimuClient(api_key or os.getenv("DIMU_API_KEY"))
        try:
            yield
        finally:
            if client is None:
                app.state.dimu.close()

    app = FastAPI(
        title="dimu",
        description="Tunn, validerande proxy som lämnar DigitaltMuseums publicerade data oförändrad.",
        version="0.2.1",
        lifespan=lifespan,
    )

    def authenticate(request: Request) -> None:
        supplied = request.headers.get("authorization", "")
        expected = f"Bearer {request.app.state.service_token}"
        if not hmac.compare_digest(supplied.encode(), expected.encode()):
            raise HTTPException(
                status_code=401,
                detail="Ogiltig Bearer-token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def dimu(request: Request) -> DimuClient:
        return request.app.state.dimu

    secured = [Depends(authenticate)]

    @app.get("/health", dependencies=secured)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/collections", dependencies=secured)
    def collections(
        countries: list[Country] = Query(
            default=[Country.SWEDEN, Country.NORWAY], min_length=1, max_length=2
        ),
        dimu_client: DimuClient = Depends(dimu),
    ) -> list[Collection]:
        result: list[Collection] = []
        for country in dict.fromkeys(countries):
            response = _upstream(lambda country=country: dimu_client.collections_raw(country))
            try:
                root = ElementTree.fromstring(response.content)
            except ElementTree.ParseError as error:
                raise HTTPException(status_code=502, detail="DigitaltMuseum returnerade ogiltig XML.") from error
            result.extend(
                Collection(
                    identifier=owner.findtext("identifier", ""),
                    name=owner.findtext("name", ""),
                    parent=owner.findtext("parent"),
                    country=country,
                )
                for owner in root.findall("owner")
            )
        return result

    @app.get("/v1/collections/{country}/raw", dependencies=secured)
    def collections_raw(country: Country, dimu_client: DimuClient = Depends(dimu)) -> Response:
        return _verbatim(_upstream(lambda: dimu_client.collections_raw(country)))

    @app.post("/v1/search", dependencies=secured)
    def search(search_request: SearchRequest, dimu_client: DimuClient = Depends(dimu)) -> Response:
        return _verbatim(_upstream(lambda: dimu_client.search(search_request)))

    @app.get("/v1/artifacts/{unique_id}", dependencies=secured)
    def artifact(
        unique_id: Annotated[str, Path(min_length=1, pattern=r".*\S.*")],
        format: ArtifactFormat = ArtifactFormat.SIMPLE_JSON,
        dimu_client: DimuClient = Depends(dimu),
    ) -> Response:
        return _verbatim(_upstream(lambda: dimu_client.artifact(unique_id, format)))

    @app.get("/v1/openai-tools", dependencies=secured)
    def tools() -> JSONResponse:
        return JSONResponse(openai_tools())

    return app


app = create_app()
