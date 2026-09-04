# HTTP-API

Alla endpoints, även hälsokontrollen, kräver:

```http
Authorization: Bearer <DIMU_SERVICE_TOKEN>
```

Interaktiv OpenAPI-dokumentation finns på `/docs` när tjänsten körs. Den
beskriver den externa tjänsten; DigitaltMuseums råa svar har avsiktligt inget
FastAPI-response-model.

## Endpoints

### `GET /health`

Kontrollerar att tjänsten har startat och att token godtas.

### `GET /v1/collections`

Returnerar en liten JSON-lista med `identifier`, `name`, `country` och `parent`.
Standard är båda länderna. Parametern kan upprepas:

```console
curl -H "Authorization: Bearer $DIMU_SERVICE_TOKEN" \
  "https://example.org/v1/collections?countries=se&countries=no"
```

### `GET /v1/collections/{country}/raw`

`country` är `se` eller `no`. Svaret är DigitaltMuseums ursprungliga XML-body.

### `POST /v1/search`

Body är `SearchRequest`:

```console
curl -X POST "https://example.org/v1/search" \
  -H "Authorization: Bearer $DIMU_SERVICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"Uppsala slott","collection_ids":["S-UM"],"limit":10}'
```

Vid framgång är body samma body som `/api/solr/select` returnerade. Ingen
`data`, `results` eller annan wrapper läggs till.

### `GET /v1/artifacts/{unique_id}`

Hämtar hela posten. Query-parametern `format` är `simple_json` (standard),
`ABM` eller `ESE`.

### `GET /v1/openai-tools`

Returnerar en JSON-lista med tre strict function tools för OpenAI Responses
API. Endpointen anropar inte OpenAI och kräver ingen OpenAI-nyckel.

## Fel

| Status | Betydelse |
| --- | --- |
| `401` | Bearer-token saknas eller är fel. |
| `422` | FastAPI/Pydantic avvisade indata. |
| `502` | DigitaltMuseum gav felstatus, nätverksfel eller ogiltig XML. |
| `504` | Anropet till DigitaltMuseum nådde sin timeout. |

Upstream-felbody, API-nyckel och råfråga återges inte i felmeddelandet. Lyckade
svar bevaras däremot utan normalisering.
