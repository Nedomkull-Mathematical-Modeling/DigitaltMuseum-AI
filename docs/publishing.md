# Release och Read the Docs

## Lokal verifiering

```console
python -m pip install -e ".[api,docs,test]" build
python -m unittest discover -s tests -v
mkdocs build --strict
python -m build
```

Det sista kommandot skapar både wheel och sdist i `dist/`.
MkDocs bygger svenska på rot-URL:en och norskt bokmål under `/no/`, med en
språkväljare i Material.

## PyPI Trusted Publishing

GitHub Actions använder OIDC och behöver ingen långlivad PyPI-token.

1. Skapa eller reservera projektet `dimu` på PyPI.
2. Lägg till en Trusted Publisher för rätt GitHub-ägare och repository.
3. Ange workflow-filen `publish.yml` och environment `pypi`.
4. Uppdatera `version` i `pyproject.toml`.
5. Skapa och pusha exakt motsvarande tagg, exempelvis `v0.2.0`.

Workflowen avbryter publiceringen om taggen och paketversionen skiljer sig. Den
testar, bygger dokumentationen strikt, bygger distributionerna och publicerar
först därefter genom `pypa/gh-action-pypi-publish`.

## Read the Docs

Repositoryt innehåller `.readthedocs.yaml` version 2. Den väljer Ubuntu 24.04,
Python 3.12, installerar `.[docs]` och kör MkDocs med varningar som fel.

I Read the Docs:

1. Importera GitHub-repositoryt som ett nytt projekt.
2. Låt tjänsten läsa konfigurationen från repositoryts rot.
3. Aktivera önskade versioner och bygg `latest`.
4. Lägg eventuellt till en egen domän i Read the Docs; canonical URL sätts
   automatiskt genom `READTHEDOCS_CANONICAL_URL`.

Inga hemligheter krävs för dokumentationsbygget eftersom det inte gör levande
anrop mot DigitaltMuseum.

## Manuellt live-smoketest

CI använder endast `httpx.MockTransport`. Före en release kan en människa med
giltig API-nyckel kontrollera:

```powershell
dimu owners --country se
dimu owners --country no
dimu search "museum" --owner S-UM --rows 1 --pictures
dimu search "museum" --owner NF --rows 1 --pictures
```

Ta sedan `artifact.uniqueId` ur svaret och kör `dimu artifact <id>`. Detta
bekräftar både en svensk och norsk samlingslista samt sök- och artifactflödet
utan att göra CI beroende av extern drift.
