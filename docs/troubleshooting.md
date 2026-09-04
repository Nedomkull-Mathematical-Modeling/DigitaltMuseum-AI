# Felsökning och begränsningar

## Servern startar inte

- `DIMU_SERVICE_TOKEN krävs`: sätt tjänstens egna delade hemlighet.
- Varning om demo-nyckeln: tjänsten fungerar, men `DIMU_API_KEY` bör sättas till
  en egen nyckel före produktionsdrift.

## HTTP-fel

- `401`: kontrollera exakt `Authorization: Bearer ...` och att inga citattecken
  följde med token.
- `422`: läs FastAPI-svarets `detail`; det visar egenskap, förväntad typ och
  valideringsregel.
- `502`: DigitaltMuseum svarade med fel, nätverket misslyckades eller owner-XML
  kunde inte tolkas. Försök igen senare och kontrollera upstream-status.
- `504`: sökningen tog längre än klientens timeout. Begränsa frågan eller
  försök igen.

## Inga träffar

1. Ta bort samlings- och årfilter och sök brett.
2. Prova `semantic_metadata` för begrepp i stället för exakta ord.
3. Kontrollera samlings-ID med `/v1/collections`.
4. Inspektera `to_params()` för att se exakt vad som skickas.
5. Använd rå Solr-syntax först när den strukturerade frågan inte kan uttrycka
   behovet.

## Datamodell och aktualitet

Institutionerna ansvarar för publicerad metadata. Fält kan saknas, vara listor,
ha lokala skrivsätt eller förändras över tid. `dimu` försöker inte harmonisera
detta. Chatboten måste skilja mellan frånvarande uppgift och ett verkligt
negativt värde.

## Licenser och bilder

Programvaran `dimu` distribueras under MIT-licensen i repositoryts `LICENSE`.
Varje posts licensfält styr återanvändning. Att posten kan hämtas via API:t
innebär inte automatiskt fri användning. Bildadresser byggs inte om av paketet;
DigitaltMuseum dokumenterar sin multimediaserver separat och bilder kan finnas
i olika maximala storlekar.

## Kända gränser

- Högst 20 sökträffar per anrop och 50 samlings-ID:n/filter per modellfält.
- Ingen automatisk retry, cache, databas, embeddinglagring eller lokal sökindex.
- Rå `q`/`fq` kan skapa dyra eller felaktiga frågor och bör bara exponeras för
  den betrodda chatbot-backenden.
- Framgångsrika search/artifact-svar är råa; paketet garanterar därför inte en
  stabil response-schemaform när DigitaltMuseum förändras.
