# Felt og objekttyper

Verdiene nedenfor er DigitaltMuseums egne feltnavn. Python-enumene hindrer
skrivefeil, men endrer ikke navnene i upstream-dataene.

## Søke- og filterfelt

| Verdi | Norsk betydning |
| --- | --- |
| `identifier.id` | Lokal identifikator hos publisisten. |
| `identifier.owner` | Identifikator for museet eller samlingen. |
| `artifact.uniqueId` | Global DigitaltMuseum-identifikator. |
| `artifact.type` | Objekttype. |
| `artifact.pictureCount` | Antall bilder. |
| `artifact.hasPictures` | Om posten har bilder. |
| `artifact.publishedDate` | Publiseringsdato. |
| `artifact.updatedDate` | Siste oppdatering. |
| `artifact.name` | Navn. |
| `artifact.title` | Tittel. |
| `artifact.classification` | Klassifikasjon. |
| `artifact.producer` | Opphavsperson eller produsent. |
| `artifact.depictedPerson` | Avbildet person. |
| `artifact.depictedPlace` | Avbildet sted. |
| `artifact.material` | Materiale. |
| `artifact.technique` | Teknikk. |
| `artifact.license` | Lisens. |
| `artifact.eventDescription` | Hendelsesbeskrivelse. |
| `artifact.event.fromYear` | Hendelsens startår. |
| `artifact.event.toYear` | Hendelsens sluttår. |
| `artifact.event.place` | Hendelsens sted. |
| `artifact.folderUids` | Mappeidentifikatorer. |
| `artifact.exhibitionUids` | Utstillingsidentifikatorer. |
| `allContent` | Søk i alt indeksert innhold. |

## Lagrede svarfelt

`return_fields` eksporteres som Solr-parameteren `fl`. Følgende verdier støttes:

```text
identifier.id
identifier.owner
artifact.uniqueId
artifact.type
artifact.pictureCount
artifact.hasPictures
artifact.defaultMediaIdentifier
artifact.publishedDate
artifact.updatedDate
artifact.ingress.title
artifact.ingress.producer
artifact.ingress.producerRole
artifact.ingress.additionalProducers
artifact.ingress.production.fromYear
artifact.ingress.production.toYear
artifact.ingress.production.place
artifact.ingress.classification
artifact.ingress.subjects
artifact.ingress.license
artifact.coordinate
```

Utelat `return_fields` for å unngå å skjule data utilsiktet for chatboten.

## Objekttyper

| Verdi | Omtrentlig kategori |
| --- | --- |
| `Thing` | Gjenstand. |
| `Photograph` | Fotografi. |
| `Architecture` | Arkitekturpost. |
| `Artdesign` | Kunst eller design. |
| `Building` | Bygning. |
| `Exhibition` | Utstilling. |
| `ExternalArticle` | Ekstern artikkel. |
| `Fineart` | Kunstverk. |
| `Folder` | Samlingsmappe. |
| `Name` | Navnepost. |
| `Person` | Personpost. |

## Fasetter

De forhåndsdefinerte fasettene er samling (`identifier.owner`), objekttype
(`artifact.type`), lisens (`artifact.ingress.license`) og emneord
(`artifact.ingress.subjects`). Upstream-resultatet beholder DigitaltMuseums egen
fasettstruktur.
