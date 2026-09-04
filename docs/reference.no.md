# Python-referanse

Denne siden oppsummerer det offentlige grensesnittet på norsk. Se
typeannotasjonene i pakken for den maskinlesbare detaljreferansen.

## `DimuClient`

```python
DimuClient(
    api_key: str | None = None,
    *,
    base_url: str = "https://api.dimu.org",
    timeout: float = 30.0,
    transport: httpx.BaseTransport | None = None,
)
```

- `search(request: SearchRequest) -> httpx.Response` kjører et søk uten å tolke
  svaret.
- `artifact(unique_id, format="simple_json") -> httpx.Response` henter en
  komplett post som `simple_json`, `ABM` eller `ESE`.
- `collections_raw(country) -> httpx.Response` henter opprinnelig owner-XML.
- `collections(country) -> list[Collection]` lager den AI-vennlige
  samlingslisten.
- `close()` lukker tilkoblingspoolen. Context manager gjør dette automatisk.

## `SearchRequest`

Modellen godtar følgende egenskaper:

| Egenskap | Type og betydning |
| --- | --- |
| `query` | Valgfri vanlig eller semantisk søketekst. |
| `mode` | `lexical`, `semantic_metadata` eller `semantic_image_content`. |
| `raw_query` | Valgfri, uendret Solr-parameter `q`. |
| `terms` | Opptil 50 strukturerte `SearchTerm`. |
| `raw_filter_queries` | Opptil 50 uendrede `fq`-uttrykk. |
| `collection_ids` | Opptil 50 publisist-/samlings-ID-er. |
| `artifact_types` | En liste med dokumenterte objekttyper. |
| `has_pictures` | `true`, `false` eller `null`. |
| `year_from`, `year_to` | Valgfritt overlappende årsintervall. |
| `image_url`, `image_base64` | Bildelikhet fra URL eller base64. |
| `similar_image_id` | Likhet med bildet til en UUID. |
| `similar_metadata_id` | Metadatalikhet med en UUID. |
| `offset`, `limit` | Paginering; `limit` er 1–20. |
| `sort` | `relevance`, `published` eller `updated`. |
| `facets` | Samling, type, lisens og/eller emneord. |
| `return_fields` | Valgfri liste med lagrede svarfelt. |

`to_params() -> list[tuple[str, str]]` validerer og eksporterer spørringen til
URL-parametere. Listen bevarer gjentatte `fq` og `facet.field`.

## `SearchTerm`

Et søkeledd har `field`, `value`, `match` (`terms` eller `phrase`) og
`occurrence` (`must` eller `must_not`). `to_filter_query()` returnerer den
beskyttede Solr-syntaksen.

## Øvrige modeller

- `ArtifactRequest` beskriver `unique_id` og outputformat for chatbotverktøyet.
- `CollectionsRequest` beskriver landene `se` og/eller `no`.
- `Collection` inneholder `identifier`, `name`, `country` og eventuell `parent`.
- `openai_tools()` returnerer tre strict-kompatible funksjonsverktøy.
- `create_app()` oppretter FastAPI-applikasjonen og validerer miljøet ved start.
