# OpenAI og chatboter

Tjenesten er et verktøy for en allerede eksisterende chatbot. Den inneholder
ingen OpenAI-klient og trenger ingen `OPENAI_API_KEY`. Verktøydefinisjonene
følger [OpenAIs offisielle veiledning for function calling](https://developers.openai.com/api/docs/guides/function-calling/):
`strict` er `true`, objekter er lukket med `additionalProperties: false`, og
alle egenskaper er required. Logisk valgfrie verdier tillater `null`.

## Hent verktøyene

```python
import httpx

service_url = "https://dimu.example.org"
headers = {"Authorization": "Bearer tjenestens-hemmelighet"}

tools = httpx.get(f"{service_url}/v1/openai-tools", headers=headers).json()
# Send listen som tools i Responses API-kallet fra den eksisterende chatboten.
```

Verktøyene heter:

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
        raise ValueError(f"Ukjent verktøy: {name}")
    response.raise_for_status()
    return response.text
```

Returner `response.text` som tool output. Da mottar modellen DigitaltMuseums
data uten et normaliserende mellomlag. Ikke begrens body ytterligere dersom
verbatim-kravet er viktigere enn tokenkostnaden.

## Komplett eksempel

Brukeren spør:

> Vis fotografier fra Oslo omkring 1920 som har et bilde.

Modellen kan først liste samlinger og identifisere `NF`. Deretter lager den
følgende strict-kompatible argumenter. Alle egenskaper er med fordi OpenAI
strict krever det:

```json
{
  "query": "Oslo",
  "mode": "lexical",
  "raw_query": null,
  "terms": [
    {
      "field": "artifact.event.place",
      "value": "Oslo",
      "match": "terms",
      "occurrence": "must"
    }
  ],
  "raw_filter_queries": [],
  "collection_ids": ["NF"],
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

Tjenesten eksporterer blant annet:

```text
q=Oslo
fq=artifact.event.place:(Oslo)
fq=(identifier.owner:"NF")
fq=(artifact.type:Photograph)
fq=artifact.hasPictures:true
fq=artifact.event.toYear:[1915 TO *]
fq=artifact.event.fromYear:[* TO 1925]
```

Hele JSON-body-en fra DigitaltMuseum returneres som tool output. Modellen leser
treffenes opprinnelige `artifact.*`- og `identifier.*`-felt, oppgir usikkerhet
og kan deretter hente en komplett post med dens `artifact.uniqueId`.

## Anbefalt chatbotinstruksjon

```text
Bruk DigitaltMuseum-verktøyene for spørsmål om norske og svenske
museumsgjenstander. Søk bredt først, og legg bare til filtre som brukeren faktisk
har oppgitt. Bruk strukturerte søkeledd når de er tilstrekkelige, og raw_query/
raw_filter_queries bare når nøyaktig Solr-syntaks er nødvendig. Behandle
verktøysvaret som rå kildedata: forstå feltenes faktiske betydning, ikke dikt opp
manglende verdier, og gjengi lisens og samling når det er relevant. Hent en
komplett post først når søketreffet ikke er tilstrekkelig.
```

## Tokenmengde

Rådata kan bli omfattende. `limit=10` er en fornuftig start, og maksimum er 20.
Bruk `offset` for å hente flere sider. `return_fields` kan redusere tokenmengden,
men innebærer bevisst at andre lagrede felt ikke returneres.
