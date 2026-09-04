# Søkeguiden

## Grunnleggende søk

```python
from dimu import DimuClient, SearchRequest

request = SearchRequest(query="fartøy i Bergen", limit=10)
with DimuClient(api_key="demo") as client:
    response = client.search(request)
```

`to_params()` kan undersøkes uten nettverkskall:

```python
request.to_params()
# [('wt', 'json'), ('start', '0'), ('rows', '10'), ('q', 'fartøy i Bergen')]
```

Metoden returnerer en liste med par, ikke en `dict`, fordi `fq` og
`facet.field` må kunne forekomme flere ganger.

## Søkemoduser

| `mode` | Upstream-parameter | Bruk |
| --- | --- | --- |
| `lexical` | `q` | Vanlig Solr-tekstsøk og eksakte ord-/feltsøk. |
| `semantic_metadata` | `metadata_q` | Semantisk likhet i postenes metadata. |
| `semantic_image_content` | `image_content_q` | Tekstbeskrivelse sammenlignet med innholdet i bildene. |

```python
from dimu import SearchMode, SearchRequest

request = SearchRequest(
    query="hester i vinterlandskap",
    mode=SearchMode.SEMANTIC_IMAGE_CONTENT,
)
```

## Strukturerte filtre

```python
from dimu import MatchMode, Occurrence, SearchField, SearchRequest, SearchTerm

request = SearchRequest(
    query="stol",
    terms=[
        SearchTerm(field=SearchField.MATERIAL, value="tre"),
        SearchTerm(
            field=SearchField.EVENT_PLACE,
            value="Oslo by",
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

Hvert søkeledd blir en separat `fq`. `terms` beskytter Solr-spesialtegn.
`phrase` setter verdien i anførselstegn; `must_not` setter minus foran filteret.

## Samlinger, typer, år og bilder

```python
from dimu import ArtifactType, SearchRequest

request = SearchRequest(
    query="kamera",
    collection_ids=["NF", "MH"],
    artifact_types=[ArtifactType.THING, ArtifactType.PHOTOGRAPH],
    has_pictures=True,
    year_from=1900,
    year_to=1950,
)
```

Flere samlinger eller typer grupperes med `OR` i hvert sitt obligatoriske
filter. Årene implementeres som intervalloverlapp: postens sluttår må være minst
`year_from`, og startåret høyst `year_to`.

## Fasetter, felt og paginering

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

`limit` er 1–20, og `offset` er nullbasert. En tom `return_fields` bruker
DigitaltMuseums standardfelt. Feltbegrensning er valgfritt og bør unngås når
chatboten trenger mest mulig komplette søkeresultater.

## Rå Solr-syntaks

```python
request = SearchRequest(
    raw_query='artifact.title:("dampmaskin" OR lokomotiv)',
    raw_filter_queries=[
        "artifact.event.fromYear:[1850 TO 1920]",
        "-artifact.material:plast",
    ],
)
```

`raw_query` sendes tegn-for-tegn som parameterverdien `q` og har prioritet
dersom `query` også angis. Hver verdi i `raw_filter_queries` sendes uendret som
`fq`. URL-koding utføres av HTTPX og endrer ikke den dekodede parameterverdien.

!!! warning
    Rå syntaks er en bevisst escape hatch. Den valideres bare som en ikke-tom
    streng. Chatboten bør velge strukturerte filtre når de er tilstrekkelige.

## Bilde- og likhetssøk

- `image_url` blir `image_url_q`.
- `image_base64` blir `image_q`.
- `similar_image_id` blir `similar_image_id`.
- `similar_metadata_id` blir `similar_metadata_id`.

Minst én av `query`, `raw_query` eller disse fire kildene kreves. Base64 for
bilder kan bli svært stor og bør normalt ikke sendes gjennom et
språkmodellverktøy; en offentlig `image_url` er mer effektiv.
