# Fält och objekttyper

Värdena nedan är DigitaltMuseums egna fältnamn. Python-enumerationerna hindrar
stavfel men byter inte namn på upstream-data.

## Sök- och filterfält

| Värde | Svensk betydelse |
| --- | --- |
| `identifier.id` | Lokal identifierare hos publicisten. |
| `identifier.owner` | Museets eller samlingens identifierare. |
| `artifact.uniqueId` | Global DigitaltMuseum-identifierare. |
| `artifact.type` | Objekttyp. |
| `artifact.pictureCount` | Antal bilder. |
| `artifact.hasPictures` | Om posten har bilder. |
| `artifact.publishedDate` | Publiceringsdatum. |
| `artifact.updatedDate` | Senaste uppdatering. |
| `artifact.name` | Namn. |
| `artifact.title` | Titel. |
| `artifact.classification` | Klassifikation. |
| `artifact.producer` | Upphovsperson eller producent. |
| `artifact.depictedPerson` | Avbildad person. |
| `artifact.depictedPlace` | Avbildad plats. |
| `artifact.material` | Material. |
| `artifact.technique` | Teknik. |
| `artifact.license` | Licens. |
| `artifact.eventDescription` | Händelsebeskrivning. |
| `artifact.event.fromYear` | Händelsens startår. |
| `artifact.event.toYear` | Händelsens slutår. |
| `artifact.event.place` | Händelsens plats. |
| `artifact.folderUids` | Mappidentifierare. |
| `artifact.exhibitionUids` | Utställningsidentifierare. |
| `allContent` | Sökning över allt indexerat innehåll. |

## Lagrade svarsfält

`return_fields` exporteras som Solr-parametern `fl`. Följande värden stöds:

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

Utelämna `return_fields` för att undvika att oavsiktligt dölja data för
chatboten.

## Objekttyper

| Värde | Ungefärlig kategori |
| --- | --- |
| `Thing` | Föremål. |
| `Photograph` | Fotografi. |
| `Architecture` | Arkitekturpost. |
| `Artdesign` | Konst eller design. |
| `Building` | Byggnad. |
| `Exhibition` | Utställning. |
| `ExternalArticle` | Extern artikel. |
| `Fineart` | Konstverk. |
| `Folder` | Samlingsmapp. |
| `Name` | Namnpost. |
| `Person` | Personpost. |

## Facetter

De fördefinierade facetterna är samling (`identifier.owner`), objekttyp
(`artifact.type`), licens (`artifact.ingress.license`) och ämnesord
(`artifact.ingress.subjects`). Upstream-resultatet behåller DigitaltMuseums
egen facetstruktur.
