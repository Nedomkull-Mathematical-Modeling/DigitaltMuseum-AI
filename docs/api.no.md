# HTTP-API

Alle endepunkter, også helsesjekken, krever:

```http
Authorization: Bearer <DIMU_SERVICE_TOKEN>
```

Interaktiv OpenAPI-dokumentasjon finnes på `/docs` når tjenesten kjører. Den
beskriver den eksterne tjenesten; DigitaltMuseums rå svar har med hensikt ingen
FastAPI-response-model.

## Endepunkter

### `GET /health`

Kontrollerer at tjenesten har startet og at tokenet godtas.

### `GET /v1/collections`

Returnerer en liten JSON-liste med `identifier`, `name`, `country` og `parent`.
Begge land brukes som standard. Parameteren kan gjentas:

```console
curl -H "Authorization: Bearer $DIMU_SERVICE_TOKEN" \
  "https://example.org/v1/collections?countries=se&countries=no"
```

### `GET /v1/collections/{country}/raw`

`country` er `se` eller `no`. Svaret er DigitaltMuseums opprinnelige XML-body.

### `POST /v1/search`

Body er en `SearchRequest`:

```console
curl -X POST "https://example.org/v1/search" \
  -H "Authorization: Bearer $DIMU_SERVICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"Oslo havn","collection_ids":["NF"],"limit":10}'
```

Ved suksess er body den samme som `/api/solr/select` returnerte. Ingen `data`,
`results` eller annen wrapper blir lagt til.

### `GET /v1/artifacts/{unique_id}`

Henter hele posten. Query-parameteren `format` er `simple_json` (standard),
`ABM` eller `ESE`.

### `GET /v1/openai-tools`

Returnerer en JSON-liste med tre strict function tools for OpenAI Responses
API. Endepunktet kaller ikke OpenAI og krever ingen OpenAI-nøkkel.

## Feil

| Status | Betydning |
| --- | --- |
| `401` | Bearer-token mangler eller er feil. |
| `422` | FastAPI/Pydantic avviste input. |
| `502` | DigitaltMuseum ga feilstatus, nettverksfeil eller ugyldig XML. |
| `504` | Kallet til DigitaltMuseum nådde tidsavbruddet. |

Upstream-feilbody, API-nøkkel og rå spørring gjengis ikke i feilmeldingen.
Vellykkede svar bevares derimot uten normalisering.
