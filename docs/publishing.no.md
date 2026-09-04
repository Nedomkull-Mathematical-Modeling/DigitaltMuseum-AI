# Publisering og Read the Docs

## Lokal verifisering

```console
python -m pip install -e ".[api,docs,test]" build
python -m unittest discover -s tests -v
mkdocs build --strict
python -m build
```

Den siste kommandoen oppretter både wheel og sdist i `dist/`. MkDocs bygger
svensk på rot-URL-en og norsk bokmål under `/no/`, med en språkvelger i Material.

## PyPI Trusted Publishing

GitHub Actions bruker OIDC og trenger ikke et langlivet PyPI-token.

1. Opprett eller reserver prosjektet `dimu` på PyPI.
2. Legg til en Trusted Publisher for riktig GitHub-eier og repository.
3. Angi workflow-filen `publish.yml` og environment `pypi`.
4. Oppdater `version` i `pyproject.toml`.
5. Opprett og push nøyaktig tilsvarende tagg, for eksempel `v0.2.0`.

Workflowen avbryter publiseringen hvis taggen og pakkeversjonen er forskjellige.
Den tester, bygger begge dokumentspråkene strengt, bygger distribusjonene og
publiserer deretter med `pypa/gh-action-pypi-publish`.

## Read the Docs

Repositoryet inneholder `.readthedocs.yaml` versjon 2. Den velger Ubuntu 24.04,
Python 3.12, installerer `.[docs]` og kjører MkDocs med advarsler som feil.

I Read the Docs:

1. Importer GitHub-repositoryet som et nytt prosjekt.
2. La tjenesten lese konfigurasjonen fra repositoryets rot.
3. Aktiver ønskede versjoner og bygg `latest`.
4. Legg eventuelt til et eget domene; canonical URL settes automatisk gjennom
   `READTHEDOCS_CANONICAL_URL`.

Ingen hemmeligheter kreves for dokumentasjonsbygget fordi det ikke gjør levende
kall mot DigitaltMuseum.

## Manuell live-smoketest

CI bruker bare `httpx.MockTransport`. Før en release kan en person med gyldig
API-nøkkel kontrollere:

```powershell
dimu owners --country se
dimu owners --country no
dimu search "museum" --owner S-UM --rows 1 --pictures
dimu search "museum" --owner NF --rows 1 --pictures
```

Ta deretter `artifact.uniqueId` fra svaret og kjør `dimu artifact <id>`. Dette
bekrefter både svenske og norske samlingslister samt søke- og artifactflyten uten
å gjøre CI avhengig av ekstern drift.
