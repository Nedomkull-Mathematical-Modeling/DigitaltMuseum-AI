# Feilsøking og begrensninger

## Serveren starter ikke

- `DIMU_SERVICE_TOKEN krävs`: sett tjenestens egen delte hemmelighet.
- Advarsel om demo-nøkkelen: tjenesten virker, men `DIMU_API_KEY` bør settes til
  en egen nøkkel før produksjonsdrift.

Feiltekstene fra programmet er foreløpig svenske; betydningen er forklart over.

## HTTP-feil

- `401`: kontroller nøyaktig `Authorization: Bearer ...`, og at anførselstegn
  ikke fulgte med tokenet.
- `422`: les `detail` i FastAPI-svaret; det viser egenskap, forventet type og
  valideringsregel.
- `502`: DigitaltMuseum svarte med feil, nettverket sviktet eller owner-XML
  kunne ikke tolkes. Prøv igjen senere og kontroller upstream-status.
- `504`: søket tok lengre tid enn klientens timeout. Begrens spørringen eller
  prøv igjen.

## Ingen treff

1. Fjern samlings- og årsfiltre og søk bredt.
2. Prøv `semantic_metadata` for begreper i stedet for eksakte ord.
3. Kontroller samlings-ID med `/v1/collections`.
4. Undersøk `to_params()` for å se nøyaktig hva som sendes.
5. Bruk rå Solr-syntaks først når den strukturerte spørringen ikke kan uttrykke
   behovet.

## Datamodell og aktualitet

Institusjonene har ansvar for publiserte metadata. Felt kan mangle, være
lister, ha lokale skrivemåter eller endres over tid. `dimu` forsøker ikke å
harmonisere dette. Chatboten må skille mellom manglende opplysning og en faktisk
negativ verdi.

## Lisenser og bilder

Programvaren `dimu` distribueres under MIT-lisensen i repositoryets `LICENSE`.
Lisensfeltet i hver post styrer gjenbruk. At posten kan hentes via API-et betyr
ikke automatisk fri bruk. Bildeadresser bygges ikke om av pakken;
DigitaltMuseum dokumenterer multimedieserveren separat, og bilder kan finnes i
ulike maksimumsstørrelser.

## Kjente grenser

- Maksimalt 20 søketreff per kall og 50 samlings-ID-er/filtre per modellfelt.
- Ingen automatisk retry, cache, database, embedding-lagring eller lokal
  søkeindeks.
- Rå `q`/`fq` kan skape kostbare eller feilaktige spørringer og bør bare
  eksponeres for den betrodde chatbot-backenden.
- Vellykkede search/artifact-svar er rå; pakken garanterer derfor ikke en stabil
  response-schemaform når DigitaltMuseum endres.
