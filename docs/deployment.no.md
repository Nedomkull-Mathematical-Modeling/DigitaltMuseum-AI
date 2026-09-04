# Drift og sikkerhet

## Automatisk installasjon på Ubuntu

Skriptet `deploy/ubuntu.sh` installerer pakken i `/opt/dimu`, kjører Uvicorn
som systembrukeren `dimu` under Supervisor, konfigurerer Nginx og henter et
Let's Encrypt-sertifikat med Certbot. Det er laget for en Ubuntu-server med
systemd og et domene der A/AAAA-posten allerede peker på serveren. Port 80 og
443 må være åpne utenfra.

Kopier eller sjekk ut prosjektet på serveren og kjør fra prosjektroten:

```console
sudo DIMU_SERVICE_TOKEN='et-langt-tilfeldig-token' \
  DIMU_API_KEY='din-produksjonsnøkkel' \
  bash deploy/ubuntu.sh api.example.no admin@example.no
```

`DIMU_SERVICE_TOKEN` er påkrevd. Hvis `DIMU_API_KEY` utelates, brukes `demo`,
og en tydelig advarsel skrives både av skriptet og når tjenesten starter.
Skriptet kan kjøres på nytt for å oppgradere installert kode. Det skriver
følgende driftsfiler:

- `/etc/dimu.env`, bare lesbar for root og gruppen `dimu`.
- `/etc/supervisor/conf.d/dimu.conf`.
- `/etc/nginx/sites-available/dimu` og en lenke i `sites-enabled`.

Kontroller driften med:

```console
sudo supervisorctl status dimu
sudo tail -f /var/log/dimu.err.log
sudo nginx -t
sudo certbot renew --dry-run
```

Ubuntu aktiverer normalt automatisk fornyelse for Certbot når snap-pakken
installeres. Testkommandoen over verifiserer hele fornyelsesflyten uten å
bytte det aktive sertifikatet.

## Container og GitHub Container Registry

Containeren kjører som en ikke-root-bruker og mottar nøkler bare gjennom
miljøvariabler ved kjøring:

```console
docker build -t dimu .
docker run --rm -p 8000:8000 \
  -e DIMU_SERVICE_TOKEN='et-langt-tilfeldig-token' \
  -e DIMU_API_KEY='demo' \
  dimu
```

Workflow-filen `.github/workflows/container.yml` kjører bare når en Git-tagg
pushes. En Git-tagg som `v0.2.0` publiserer containertaggene `v0.2.0` og
`latest` og oppretter en GitHub Release med automatisk genererte
versjonsnotater. Containeren publiseres til:

```text
ghcr.io/nedomkull-mathematical-modeling/digitaltmuseum-ai:<tagg>
```

Hver tagg er et manifest for de vanligste Linux-arkitekturene: `linux/amd64`
og `linux/arm64`. Docker velger automatisk riktig image for vertsmaskinen.

Publiseringen bruker repositoryets kortlivede `GITHUB_TOKEN` med
`packages: write`; ingen separat registry-hemmelighet er nødvendig. Imaget er
offentlig og kan derfor hentes uten GitHub-innlogging. Synligheten håndteres
under **Packages** i GitHub. Kjør det publiserte imaget slik:

```console
docker pull ghcr.io/nedomkull-mathematical-modeling/digitaltmuseum-ai:latest
docker run --rm -p 8000:8000 \
  -e DIMU_SERVICE_TOKEN='et-langt-tilfeldig-token' \
  ghcr.io/nedomkull-mathematical-modeling/digitaltmuseum-ai:latest
```

## Start prosessen

```console
uvicorn dimu.api:app --host 127.0.0.1 --port 8000 --workers 2
```

Bruk en prosesshåndterer eller containerplattform som starter prosessen på nytt
ved feil. Hver worker har sin egen tilkoblingspool mot DigitaltMuseum.

## TLS og reverse proxy

Uvicorn bør normalt lytte på localhost eller et privat nett. La en etablert
reverse proxy eller skyplattform terminere TLS og videresende HTTPS-trafikken.
Send aldri `DIMU_SERVICE_TOKEN` over ukryptert internettrafikk.

Proxykonfigurasjonen må tillate:

- `Authorization`-headeren.
- POST-body som rommer valgt maksimal base64-bildestørrelse, dersom funksjonen
  brukes.
- minst 35 sekunders upstream-timeout rundt tjenestens 30 sekunder.

## Hemmeligheter

- Opprett en separat DigitaltMuseum-nøkkel i henhold til vilkårene deres.
- Bruk et langt, tilfeldig `DIMU_SERVICE_TOKEN`, og roter det ved mistanke om
  eksponering.
- Gi tokenet bare til chatbotens backend, aldri til en nettleserklient.
- Logg endepunkt, status og varighet, men ikke Authorization, `api.key`,
  base64-bilder, rå `q` eller `fq`.

## Helsesjekk

`/health` er bevisst beskyttet. Plattformens helsesjekk må derfor få
Bearer-token, eller kontrollere TCP-/prosesstatus i stedet.

## Skalering

Tjenesten har ingen database og ingen lokal tilstand. Flere instanser kan
kjøres bak en lastbalanserer. Innfør cache eller kø først når målte behov
begrunner det; caching kan ellers gjøre publiserte endringer utdaterte og
motarbeide transparenskravet.
