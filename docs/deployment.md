# Drift och säkerhet

## Automatisk installation på Ubuntu

Skriptet `deploy/ubuntu.sh` installerar paketet i `/opt/dimu`, kör Uvicorn som
systemanvändaren `dimu` under Supervisor, konfigurerar Nginx och hämtar ett
Let's Encrypt-certifikat med Certbot. Det är avsett för en Ubuntu-server med
systemd och en domän vars A/AAAA-post redan pekar på servern. Port 80 och 443
måste vara öppna utifrån.

Kopiera eller checka ut projektet på servern och kör från projektroten:

```console
sudo DIMU_SERVICE_TOKEN='en-lång-slumpmässig-token' \
  DIMU_API_KEY='din-produktionsnyckel' \
  bash deploy/ubuntu.sh api.example.se admin@example.se
```

`DIMU_SERVICE_TOKEN` krävs. Utelämnas `DIMU_API_KEY` används `demo`, och en
tydlig varning skrivs både av skriptet och när tjänsten startar. Skriptet kan
köras igen för att uppgradera den installerade koden. Det skriver följande
driftfiler:

- `/etc/dimu.env`, läsbar endast av root och gruppen `dimu`.
- `/etc/supervisor/conf.d/dimu.conf`.
- `/etc/nginx/sites-available/dimu` och en länk i `sites-enabled`.

Kontrollera driften med:

```console
sudo supervisorctl status dimu
sudo tail -f /var/log/dimu.err.log
sudo nginx -t
sudo certbot renew --dry-run
```

Ubuntu aktiverar normalt Certbots automatiska förnyelse när snap-paketet
installeras. Testkommandot ovan verifierar hela förnyelseflödet utan att byta
det aktiva certifikatet.

## Container och GitHub Container Registry

Containern kör som en icke-root-användare och tar emot nycklar endast via
miljövariabler vid körning:

```console
docker build -t dimu .
docker run --rm -p 8000:8000 \
  -e DIMU_SERVICE_TOKEN='en-lång-slumpmässig-token' \
  -e DIMU_API_KEY='demo' \
  dimu
```

Workflow-filen `.github/workflows/container.yml` körs endast när en Git-tagg
pushas. En Git-tagg som `v0.2.0` publicerar containertaggarna `v0.2.0` och
`latest` och skapar en GitHub Release med automatiskt genererade
versionsanteckningar. Containern publiceras till:

```text
ghcr.io/nedomkull-mathematical-modeling/digitaltmuseum-ai:<tagg>
```

Varje tagg är ett manifest för de vanligaste Linux-arkitekturerna:
`linux/amd64` och `linux/arm64`. Docker väljer automatiskt rätt image för
värddatorn.

Publiceringen använder repositoryts kortlivade `GITHUB_TOKEN` med
`packages: write`; ingen separat registry-hemlighet behövs. Imagen är publik
och kan därför hämtas utan GitHub-inloggning. Synligheten hanteras under
**Packages** i GitHub. Kör den publicerade imagen så här:

```console
docker pull ghcr.io/nedomkull-mathematical-modeling/digitaltmuseum-ai:latest
docker run --rm -p 8000:8000 \
  -e DIMU_SERVICE_TOKEN='en-lång-slumpmässig-token' \
  ghcr.io/nedomkull-mathematical-modeling/digitaltmuseum-ai:latest
```

## Starta processen

```console
uvicorn dimu.api:app --host 127.0.0.1 --port 8000 --workers 2
```

Använd en processhanterare eller containerplattform som startar om processen
vid fel. Varje worker har en egen anslutningspool mot DigitaltMuseum.

## TLS och reverse proxy

Uvicorn bör normalt lyssna på localhost eller ett privat nät. Låt en etablerad
reverse proxy eller molnplattform avsluta TLS och vidarebefordra HTTPS-trafik.
Skicka aldrig `DIMU_SERVICE_TOKEN` över okrypterad internettrafik.

Proxykonfigurationen måste tillåta:

- `Authorization`-rubriken.
- POST-body som rymmer vald maximal bild-base64, om den funktionen används.
- minst 35 sekunders upstream-timeout runt tjänstens 30 sekunder.

## Hemligheter

- Skapa en separat DigitaltMuseum-nyckel enligt deras villkor.
- Använd en lång slumpmässig `DIMU_SERVICE_TOKEN` och rotera den vid misstänkt
  exponering.
- Ge token endast till chatbotens backend, aldrig till en webbläsarklient.
- Logga endpoint, status och varaktighet, men inte Authorization, `api.key`,
  base64-bilder, rå `q` eller `fq`.

## Hälsokontroll

`/health` är medvetet skyddad. Plattformens hälsokontroll behöver därför få
Bearer-token, eller kontrollera TCP/processstatus i stället.

## Skalning

Tjänsten har ingen databas och inget lokalt tillstånd. Fler instanser kan
köras bakom en lastbalanserare. Inför cache eller kö först när uppmätta behov
motiverar det; cachning kan annars göra publicerade ändringar inaktuella och
motverka transparenskravet.
