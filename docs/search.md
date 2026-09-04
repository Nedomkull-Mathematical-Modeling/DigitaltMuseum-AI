# Sökguiden

## Grundläggande sökning

```python
from dimu import DimuClient, SearchRequest

request = SearchRequest(query="fartyg i Göteborg", limit=10)
with DimuClient(api_key="demo") as client:
    response = client.search(request)
```

`to_params()` kan inspekteras utan nätverksanrop:

```python
request.to_params()
# [('wt', 'json'), ('start', '0'), ('rows', '10'), ('q', 'fartyg i Göteborg')]
```

Metoden returnerar en lista av par, inte en `dict`, eftersom `fq` och
`facet.field` måste kunna förekomma flera gånger.

## Söklägen

| `mode` | Upstream-parameter | Användning |
| --- | --- | --- |
| `lexical` | `q` | Vanlig Solr-textsökning och exakta ord/fältsökningar. |
| `semantic_metadata` | `metadata_q` | Semantisk likhet i posternas metadata. |
| `semantic_image_content` | `image_content_q` | Textbeskrivning jämförd med bildernas innehåll. |

```python
from dimu import SearchMode, SearchRequest

request = SearchRequest(
    query="hästar i vinterlandskap",
    mode=SearchMode.SEMANTIC_IMAGE_CONTENT,
)
```

## Strukturerade filter

```python
from dimu import MatchMode, Occurrence, SearchField, SearchRequest, SearchTerm

request = SearchRequest(
    query="stol",
    terms=[
        SearchTerm(field=SearchField.MATERIAL, value="trä"),
        SearchTerm(
            field=SearchField.EVENT_PLACE,
            value="Stockholms stad",
            match=MatchMode.PHRASE,
        ),
        SearchTerm(
            field=SearchField.TECHNIQUE,
            value="plast",
            occurrence=Occurrence.MUST_NOT,
        ),
    ],
)
```

Varje term blir en separat `fq`. `terms` escapes Solr-specialtecken. `phrase`
omger värdet med citattecken; `must_not` prefixar filtret med minus.

## Samlingar, typer, år och bilder

```python
from dimu import ArtifactType, SearchRequest

request = SearchRequest(
    query="kamera",
    collection_ids=["S-UM", "S-AM"],
    artifact_types=[ArtifactType.THING, ArtifactType.PHOTOGRAPH],
    has_pictures=True,
    year_from=1900,
    year_to=1950,
)
```

Flera samlingar eller typer grupperas med `OR` i varsitt obligatoriskt filter.
Åren implementeras som intervallöverlappning: postens slutår måste vara minst
`year_from` och dess startår högst `year_to`.

## Facetter, fält och paginering

```python
from dimu import FacetField, SortOrder, StoredField

request = SearchRequest(
    query="uniform",
    offset=20,
    limit=20,
    sort=SortOrder.UPDATED,
    facets=[FacetField.COLLECTION, FacetField.TYPE],
    return_fields=[StoredField.UNIQUE_ID, StoredField.TITLE],
)
```

`limit` är 1–20 och `offset` är nollbaserad. Tom `return_fields` använder
DigitaltMuseums standardfält. Att begränsa fälten är frivilligt och bör inte
göras när chatboten behöver så komplett sökdata som möjligt.

## Rå Solr-syntax

```python
request = SearchRequest(
    raw_query='artifact.title:("ångmaskin" OR lokomotiv)',
    raw_filter_queries=[
        "artifact.event.fromYear:[1850 TO 1920]",
        "-artifact.material:plast",
    ],
)
```

`raw_query` skickas byte-för-byte som parameter-värdet `q` och har företräde om
`query` också anges. Varje `raw_filter_queries` skickas oförändrad som `fq`.
URL-kodning utförs av HTTPX; den ändrar inte det avkodade parametervärdet.

!!! warning
    Rå syntax är en avsiktlig escape hatch. Den valideras endast som en icke-tom
    sträng. Chatboten bör välja strukturerade filter när de räcker.

## Bild- och likhetssökning

- `image_url` blir `image_url_q`.
- `image_base64` blir `image_q`.
- `similar_image_id` blir `similar_image_id`.
- `similar_metadata_id` blir `similar_metadata_id`.

Minst en av `query`, `raw_query` eller dessa fyra källor krävs. Bild-base64 kan
vara mycket stor och bör normalt inte skickas genom ett språkmodellsverktyg;
en publik `image_url` är effektivare.
