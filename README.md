# dimu - Digitalt Museum-klient och FastAPI-proxy

`dimu` är en transparent Python-klient och en valfri FastAPI-proxy för
[DigitaltMuseums publika API](https://store-search.dimu.org/docs). Indata
valideras med Pydantic, men lyckade sök- och objektsvar lämnas orörda.

```python
from dimu import DimuClient, SearchRequest, SearchTerm

with DimuClient() as client:  # använder demo och varnar om DIMU_API_KEY saknas
    response = client.search(SearchRequest(query="Uppsala slott", limit=5))
    response.raise_for_status()
    print(response.json())
```

Installera biblioteket med `pip install dimu`. För HTTP-tjänsten används
`pip install "dimu[api]"` och följande miljövariabler:

```text
DIMU_API_KEY=<valfri produktionsnyckel från DigitaltMuseum>
DIMU_SERVICE_TOKEN=<lång slumpmässig token>
```

Starta sedan tjänsten:

```console
uvicorn dimu.api:app --host 127.0.0.1 --port 8000
```

För en Ubuntu-server med Supervisor, Nginx och Let's Encrypt:

```console
sudo DIMU_SERVICE_TOKEN='byt-mig' DIMU_API_KEY='demo' \
  bash deploy/ubuntu.sh api.example.se admin@example.se
```

En container kan byggas med `docker build -t dimu .` och köras med
`docker run --rm -p 8000:8000 -e DIMU_SERVICE_TOKEN='byt-mig' dimu`.
GitHub Actions publicerar Git-taggen och `latest` till GitHub Container
Registry och skapar en GitHub Release när en Git-tagg pushas.

Fullständig dokumentation på svenska och norskt bokmål finns i katalogen
`docs/` och byggs med `mkdocs build --strict`. Tester körs med
`python -m unittest discover -s tests -v`.

Programvaran är licensierad under MIT. Metadata och bilder får återanvändas
enligt licensen i respektive post. Paketet är ingen lokal spegel och lagrar
inte DigitaltMuseums data.
