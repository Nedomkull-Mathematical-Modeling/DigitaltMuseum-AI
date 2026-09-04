# OpenAI och chatbotar

Tjänsten är ett verktyg åt en redan existerande chatbot. Den innehåller ingen
OpenAI-klient och behöver ingen `OPENAI_API_KEY`. Verktygsdefinitionerna följer
[OpenAI:s officiella guide för function calling](https://developers.openai.com/api/docs/guides/function-calling/):
`strict` är `true`, objekt är stängda med `additionalProperties: false` och
samtliga egenskaper är required. Logiskt valfria värden tillåter `null`.

## Hämta verktygen

```python
import httpx

service_url = "https://dimu.example.org"
headers = {"Authorization": "Bearer tjänstens-hemlighet"}

tools = httpx.get(f"{service_url}/v1/openai-tools", headers=headers).json()
# Skicka listan som tools till Responses API-anropet i den befintliga chatboten.
```

Verktygen heter:

- `search_digitaltmuseum`
- `get_digitaltmuseum_artifact`
- `list_digitaltmuseum_collections`

## Dispatcher i chatbotens backend

```python
def run_dimu_tool(name: str, arguments: dict):
    if name == "search_digitaltmuseum":
        response = httpx.post(
            f"{service_url}/v1/search",
            headers=headers,
            json=arguments,
            timeout=35,
        )
    elif name == "get_digitaltmuseum_artifact":
        response = httpx.get(
            f"{service_url}/v1/artifacts/{arguments['unique_id']}",
            headers=headers,
            params={"format": arguments["format"]},
            timeout=35,
        )
    elif name == "list_digitaltmuseum_collections":
        response = httpx.get(
            f"{service_url}/v1/collections",
            headers=headers,
            params=[("countries", country) for country in arguments["countries"]],
            timeout=35,
        )
    else:
        raise ValueError(f"Okänt verktyg: {name}")
    response.raise_for_status()
    return response.text
```

Returnera `response.text` som tool output. Då får modellen DigitaltMuseums data
utan ett normaliserande mellanlager. Begränsa inte body ytterligare om
verbatim-kravet är viktigare än tokenkostnaden.

## Komplett exempel

Användaren frågar:

> Visa fotografier från Uppsala omkring 1920 som har en bild.

Modellen kan först lista samlingar och identifiera `S-UM`. Därefter skapar den
följande strict-kompatibla argument. Alla egenskaper finns med eftersom OpenAI
strict kräver det:

```json
{
  "query": "Uppsala",
  "mode": "lexical",
  "raw_query": null,
  "terms": [
    {
      "field": "artifact.event.place",
      "value": "Uppsala",
      "match": "terms",
      "occurrence": "must"
    }
  ],
  "raw_filter_queries": [],
  "collection_ids": ["S-UM"],
  "artifact_types": ["Photograph"],
  "has_pictures": true,
  "year_from": 1915,
  "year_to": 1925,
  "image_url": null,
  "image_base64": null,
  "similar_image_id": null,
  "similar_metadata_id": null,
  "offset": 0,
  "limit": 10,
  "sort": "relevance",
  "facets": [],
  "return_fields": []
}
```

Tjänsten exporterar bland annat:

```text
q=Uppsala
fq=artifact.event.place:(Uppsala)
fq=(identifier.owner:"S\-UM")
fq=(artifact.type:Photograph)
fq=artifact.hasPictures:true
fq=artifact.event.toYear:[1915 TO *]
fq=artifact.event.fromYear:[* TO 1925]
```

DigitaltMuseums hela JSON-body returneras som tool output. Modellen läser
träffarnas ursprungliga `artifact.*`- och `identifier.*`-fält, anger osäkerheter
och kan därefter hämta en full post med dess `artifact.uniqueId`.

## Rekommenderad chatbotinstruktion

```text
Använd DigitaltMuseum-verktygen för frågor om svenska och norska museiföremål.
Sök brett först och lägg bara till filter som användaren faktiskt har angett.
Använd strukturerade termer när de räcker och raw_query/raw_filter_queries endast
när exakt Solr-syntax behövs. Behandla verktygssvaret som rå källdata: hitta
fältens faktiska betydelse, hitta inte på saknade värden och återge licens och
samling när det är relevant. Hämta full post först när sökträffen inte räcker.
```

## Tokenmängd

Rådata kan bli omfattande. `limit=10` är en rimlig start och maxvärdet är 20.
Paginera med `offset` när fler träffar behövs. `return_fields` kan minska
tokenmängden, men innebär medvetet att andra lagrade fält inte returneras.
