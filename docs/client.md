# Python-klienten

## Livscykel

Använd helst klienten som context manager. Samma `httpx.Client` och dess
anslutningspool används då för alla anrop.

```python
from dimu import DimuClient, SearchRequest

with DimuClient(api_key="demo") as client:
    response = client.search(SearchRequest(query="järnvägsstation", limit=10))
    response.raise_for_status()
    data = response.json()
```

Utelämnas `api_key` läses `DIMU_API_KEY`. Om även miljövariabeln saknas används
`demo` och en `RuntimeWarning` skrivs när klienten skapas. En uttrycklig
`api_key="demo"` ger samma varning.

## Råa svar

`search()`, `artifact()` och `collections_raw()` returnerar alltid
`httpx.Response`:

```python
response.content       # bytes efter eventuell HTTP-dekomprimering
response.text          # text enligt svarets teckenkodning
response.json()        # frivillig JSON-tolkning hos anroparen
response.headers       # upstream-rubriker som httpx såg
response.status_code
```

Klienten anropar inte `raise_for_status()` automatiskt. Det gör att både body
och status kan inspekteras utan informationsförlust. Anropa metoden själv när
ett undantag passar programmets felhantering.

## Fullständigt objekt

```python
from dimu import ArtifactFormat, DimuClient

with DimuClient(api_key="demo") as client:
    json_response = client.artifact("021018621650")
    abm_response = client.artifact("021018621650", ArtifactFormat.ABM)
    ese_response = client.artifact("021018621650", ArtifactFormat.ESE)
```

Giltiga format är `simple_json`, `ABM` och `ESE`. Innehållet kommer direkt från
DigitaltMuseums artifact-endpoint.

## Samlingar

```python
with DimuClient(api_key="demo") as client:
    xml_response = client.collections_raw("se")
    parsed = client.collections("no")
```

`collections()` är en bekvämlighetsfunktion som endast returnerar `identifier`,
`name`, `country` och eventuell `parent`. Använd `collections_raw()` när XML ska
bevaras exakt.
