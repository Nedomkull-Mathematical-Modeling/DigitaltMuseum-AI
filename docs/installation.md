# Installation och konfiguration

## Krav

- Python 3.10 eller senare.
- En egen API-nyckel från DigitaltMuseum rekommenderas för normal drift. Om den
  saknas används `demo` automatiskt och en varning skrivs vid start.
- En separat, lång och slumpmässig Bearer-token om FastAPI-tjänsten används.

## Installationsvarianter

```console
# Endast Python-klienten
python -m pip install dimu

# Klient och HTTP-API
python -m pip install "dimu[api]"

# Lokal utveckling av allt
python -m pip install -e ".[api,docs,test]"
```

## Miljövariabler

| Variabel | Krävs | Betydelse |
| --- | --- | --- |
| `DIMU_API_KEY` | Nej | Produktionsnyckeln som skickas som `api.key`; standardvärdet är `demo`. |
| `DIMU_SERVICE_TOKEN` | Ja för server | Delad hemlighet för tjänstens Bearer-autentisering. |
| `READTHEDOCS_CANONICAL_URL` | Sätts av RTD | Canonical URL som MkDocs använder vid dokumentationsbygget. |

PowerShell-exempel för en lokal testserver:

```powershell
$env:DIMU_SERVICE_TOKEN = "byt-till-en-lang-slumpmassig-token"
uvicorn dimu.api:app --host 127.0.0.1 --port 8000
```

Lägg aldrig nycklar i Python-kod, Git eller dokumentation. I produktion bör de
komma från plattformens secret manager.

## Snabb kontroll

```console
curl -H "Authorization: Bearer $DIMU_SERVICE_TOKEN" http://127.0.0.1:8000/health
```

Svaret är `{"status":"ok"}`. Servern vägrar starta om tjänstens Bearer-token
saknas. Om `DIMU_API_KEY` saknas startar den med demo-nyckeln och skriver en
`RuntimeWarning`; sätt en egen nyckel före produktionsdrift.
