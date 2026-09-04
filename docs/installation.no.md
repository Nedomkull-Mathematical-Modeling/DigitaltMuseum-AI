# Installasjon og konfigurasjon

## Krav

- Python 3.10 eller nyere.
- En egen API-nøkkel fra DigitaltMuseum anbefales for vanlig drift. Hvis den
  mangler, brukes `demo` automatisk, og en advarsel skrives ved oppstart.
- Et separat, langt og tilfeldig Bearer-token dersom FastAPI-tjenesten brukes.

## Installasjonsvarianter

```console
# Bare Python-klienten
python -m pip install dimu

# Klient og HTTP-API
python -m pip install "dimu[api]"

# Lokal utvikling av alt
python -m pip install -e ".[api,docs,test]"
```

## Miljøvariabler

| Variabel | Påkrevd | Betydning |
| --- | --- | --- |
| `DIMU_API_KEY` | Nei | Produksjonsnøkkelen som sendes som `api.key`; standardverdien er `demo`. |
| `DIMU_SERVICE_TOKEN` | Ja for server | Delt hemmelighet for tjenestens Bearer-autentisering. |
| `READTHEDOCS_CANONICAL_URL` | Settes av RTD | Kanonisk URL som MkDocs bruker under dokumentasjonsbygget. |

PowerShell-eksempel for en lokal testserver:

```powershell
$env:DIMU_SERVICE_TOKEN = "bytt-til-et-langt-tilfeldig-token"
uvicorn dimu.api:app --host 127.0.0.1 --port 8000
```

Legg aldri nøkler i Python-kode, Git eller dokumentasjon. I produksjon bør de
hentes fra plattformens secret manager.

## Rask kontroll

```console
curl -H "Authorization: Bearer $DIMU_SERVICE_TOKEN" http://127.0.0.1:8000/health
```

Svaret er `{"status":"ok"}`. Serveren nekter å starte dersom tjenestens
Bearer-token mangler. Hvis `DIMU_API_KEY` mangler, starter den med demo-nøkkelen
og skriver en `RuntimeWarning`; sett en egen nøkkel før produksjonsdrift.
