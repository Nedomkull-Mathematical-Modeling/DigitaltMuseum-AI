# Python-klienten

## Livssyklus

Bruk helst klienten som context manager. Da brukes samme `httpx.Client` og
tilkoblingspool for alle kall.

```python
from dimu import DimuClient, SearchRequest

with DimuClient(api_key="demo") as client:
    response = client.search(SearchRequest(query="jernbanestasjon", limit=10))
    response.raise_for_status()
    data = response.json()
```

Dersom `api_key` utelates, leses `DIMU_API_KEY`. Hvis miljøvariabelen også
mangler, brukes `demo`, og en `RuntimeWarning` skrives når klienten opprettes.
En eksplisitt `api_key="demo"` gir samme advarsel.

## Rå svar

`search()`, `artifact()` og `collections_raw()` returnerer alltid
`httpx.Response`:

```python
response.content       # bytes etter eventuell HTTP-dekomprimering
response.text          # tekst i henhold til svarets tegnkoding
response.json()        # valgfri JSON-tolking hos kalleren
response.headers       # upstream-headere som httpx mottok
response.status_code
```

Klienten kaller ikke `raise_for_status()` automatisk. Dermed kan både body og
status undersøkes uten informasjonstap. Kall metoden selv når et unntak passer
programmets feilhåndtering.

## Komplett objekt

```python
from dimu import ArtifactFormat, DimuClient

with DimuClient(api_key="demo") as client:
    json_response = client.artifact("021018621650")
    abm_response = client.artifact("021018621650", ArtifactFormat.ABM)
    ese_response = client.artifact("021018621650", ArtifactFormat.ESE)
```

Gyldige formater er `simple_json`, `ABM` og `ESE`. Innholdet kommer direkte fra
DigitaltMuseums artifact-endepunkt.

## Samlinger

```python
with DimuClient(api_key="demo") as client:
    xml_response = client.collections_raw("se")
    parsed = client.collections("no")
```

`collections()` er en hjelpefunksjon som bare returnerer `identifier`, `name`,
`country` og eventuell `parent`. Bruk `collections_raw()` når XML skal bevares
nøyaktig.
