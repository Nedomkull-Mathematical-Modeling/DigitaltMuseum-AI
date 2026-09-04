"""Pydantic-modeller för validerade parametrar till DigitaltMuseum."""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, model_validator

NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
OwnerId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
RawExpression = Annotated[str, StringConstraints(min_length=1)]


class ValueEnum(str, Enum):
    """Sträng-enum vars strängform är dess värde."""

    def __str__(self) -> str:
        return self.value


class SearchMode(ValueEnum):
    """Tillgängliga sätt att tolka en textsökning."""

    LEXICAL = "lexical"
    SEMANTIC_METADATA = "semantic_metadata"
    SEMANTIC_IMAGE_CONTENT = "semantic_image_content"


class MatchMode(ValueEnum):
    """Hur ett strukturerat fältvärde ska matchas."""

    TERMS = "terms"
    PHRASE = "phrase"


class Occurrence(ValueEnum):
    """Om filtret ska krävas eller uteslutas."""

    MUST = "must"
    MUST_NOT = "must_not"


class SearchField(ValueEnum):
    """DigitaltMuseums sökfält: id, samling, typ, namn, titel, klassifikation,
    producent, avbildad person/plats, material, teknik, licens, händelse,
    tidsintervall, plats, mappar, utställningar eller allt innehåll.
    """

    IDENTIFIER_ID = "identifier.id"
    IDENTIFIER_OWNER = "identifier.owner"
    UNIQUE_ID = "artifact.uniqueId"
    TYPE = "artifact.type"
    PICTURE_COUNT = "artifact.pictureCount"
    HAS_PICTURES = "artifact.hasPictures"
    PUBLISHED_DATE = "artifact.publishedDate"
    UPDATED_DATE = "artifact.updatedDate"
    NAME = "artifact.name"
    TITLE = "artifact.title"
    CLASSIFICATION = "artifact.classification"
    PRODUCER = "artifact.producer"
    DEPICTED_PERSON = "artifact.depictedPerson"
    DEPICTED_PLACE = "artifact.depictedPlace"
    MATERIAL = "artifact.material"
    TECHNIQUE = "artifact.technique"
    LICENSE = "artifact.license"
    EVENT_DESCRIPTION = "artifact.eventDescription"
    EVENT_FROM_YEAR = "artifact.event.fromYear"
    EVENT_TO_YEAR = "artifact.event.toYear"
    EVENT_PLACE = "artifact.event.place"
    FOLDER_UIDS = "artifact.folderUids"
    EXHIBITION_UIDS = "artifact.exhibitionUids"
    ALL_CONTENT = "allContent"


class StoredField(ValueEnum):
    """Lagrade svarsfält för identitet, typ, bilder, datum, titel, producenter,
    produktionstid/plats, klassifikation, ämnesord, licens och koordinat.
    """

    IDENTIFIER_ID = "identifier.id"
    IDENTIFIER_OWNER = "identifier.owner"
    UNIQUE_ID = "artifact.uniqueId"
    TYPE = "artifact.type"
    PICTURE_COUNT = "artifact.pictureCount"
    HAS_PICTURES = "artifact.hasPictures"
    DEFAULT_MEDIA_IDENTIFIER = "artifact.defaultMediaIdentifier"
    PUBLISHED_DATE = "artifact.publishedDate"
    UPDATED_DATE = "artifact.updatedDate"
    TITLE = "artifact.ingress.title"
    PRODUCER = "artifact.ingress.producer"
    PRODUCER_ROLE = "artifact.ingress.producerRole"
    ADDITIONAL_PRODUCERS = "artifact.ingress.additionalProducers"
    PRODUCTION_FROM_YEAR = "artifact.ingress.production.fromYear"
    PRODUCTION_TO_YEAR = "artifact.ingress.production.toYear"
    PRODUCTION_PLACE = "artifact.ingress.production.place"
    CLASSIFICATION = "artifact.ingress.classification"
    SUBJECTS = "artifact.ingress.subjects"
    LICENSE = "artifact.ingress.license"
    COORDINATE = "artifact.coordinate"


class ArtifactType(ValueEnum):
    """Dokumenterade typer: föremål, fotografi, arkitektur, konst/design,
    byggnad, utställning, extern artikel, konstverk, mapp, namn eller person.
    """

    THING = "Thing"
    PHOTOGRAPH = "Photograph"
    ARCHITECTURE = "Architecture"
    ARTDESIGN = "Artdesign"
    BUILDING = "Building"
    EXHIBITION = "Exhibition"
    EXTERNAL_ARTICLE = "ExternalArticle"
    FINEART = "Fineart"
    FOLDER = "Folder"
    NAME = "Name"
    PERSON = "Person"


class FacetField(ValueEnum):
    """Gruppera träffantal efter samling, objekttyp, licens eller ämnesord."""

    COLLECTION = "identifier.owner"
    TYPE = "artifact.type"
    LICENSE = "artifact.ingress.license"
    SUBJECTS = "artifact.ingress.subjects"


class SortOrder(ValueEnum):
    """Fördefinierade säkra sorteringar."""

    RELEVANCE = "relevance"
    PUBLISHED = "published"
    UPDATED = "updated"


class ArtifactFormat(ValueEnum):
    """Dokumenterade format för ett fullständigt objekt."""

    SIMPLE_JSON = "simple_json"
    ABM = "ABM"
    ESE = "ESE"


class Country(ValueEnum):
    """Länder som ingår i denna tjänst."""

    SWEDEN = "se"
    NORWAY = "no"


_SOLR_SPECIAL = re.compile(r"(&&|\|\||[+\-!(){}\[\]^\"~*?:\\/])")


def escape_solr(value: str) -> str:
    """Escape Solr-specialtecken i ett strukturerat värde."""
    return _SOLR_SPECIAL.sub(r"\\\1", value)


class SearchTerm(BaseModel):
    """Ett validerat fältfilter som kompileras till en separat ``fq``."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    field: SearchField = Field(description="DigitaltMuseum-fältet som ska filtreras.")
    value: NonEmpty = Field(description="Värdet som ska sökas i det valda fältet.")
    match: MatchMode = Field(
        default=MatchMode.TERMS,
        description="terms söker orden; phrase kräver frasen i angiven ordning.",
    )
    occurrence: Occurrence = Field(
        default=Occurrence.MUST,
        description="must kräver träff; must_not utesluter träff.",
    )

    def to_filter_query(self) -> str:
        """Returnera filtret i Solr-syntax."""
        value = escape_solr(self.value)
        expression = (
            f'{self.field.value}:"{value}"'
            if self.match is MatchMode.PHRASE
            else f"{self.field.value}:({value})"
        )
        return f"-{expression}" if self.occurrence is Occurrence.MUST_NOT else expression


class SearchRequest(BaseModel):
    """En komplett, validerad sökning mot DigitaltMuseums Solr-endpoint."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    query: NonEmpty | None = Field(
        default=None,
        description="Fri söktext. Använd svenska eller norska ord från användarens fråga.",
    )
    mode: SearchMode = Field(
        default=SearchMode.LEXICAL,
        description="Lexikal sökning eller semantisk sökning i metadata respektive bildinnehåll.",
    )
    raw_query: RawExpression | None = Field(
        default=None,
        description="Avancerad Solr-fråga som skickas oförändrad som q och ersätter query.",
    )
    terms: list[SearchTerm] = Field(
        default_factory=list,
        max_length=50,
        description="Strukturerade fältfilter som escapes och skickas som separata fq.",
    )
    raw_filter_queries: list[RawExpression] = Field(
        default_factory=list,
        max_length=50,
        description="Avancerade Solr-filter som skickas oförändrade som upprepade fq.",
    )
    collection_ids: list[OwnerId] = Field(
        default_factory=list,
        max_length=50,
        description="Identifierare för svenska eller norska museer/samlingar; tom lista söker i hela katalogen.",
    )
    artifact_types: list[ArtifactType] = Field(
        default_factory=list,
        description="Objekttyper som får förekomma i resultatet.",
    )
    has_pictures: bool | None = Field(
        default=None,
        description="true kräver bilder, false kräver poster utan bilder, null filtrerar inte.",
    )
    year_from: int | None = Field(
        default=None,
        ge=-9999,
        le=9999,
        description="Tidigaste år som objektets händelseintervall får överlappa.",
    )
    year_to: int | None = Field(
        default=None,
        ge=-9999,
        le=9999,
        description="Senaste år som objektets händelseintervall får överlappa.",
    )
    image_url: HttpUrl | None = Field(
        default=None,
        description="Publik bild-URL för likhetsökning via image_url_q.",
    )
    image_base64: NonEmpty | None = Field(
        default=None,
        description="Base64-kodad bild för likhetsökning via image_q.",
    )
    similar_image_id: NonEmpty | None = Field(
        default=None,
        description="UUID vars bild ska användas för en likhetsökning.",
    )
    similar_metadata_id: NonEmpty | None = Field(
        default=None,
        description="UUID vars metadata ska användas för en semantisk likhetsökning.",
    )
    offset: int = Field(default=0, ge=0, description="Antal träffar som hoppas över.")
    limit: int = Field(default=10, ge=1, le=20, description="Antal träffar som returneras, högst 20.")
    sort: SortOrder = Field(default=SortOrder.RELEVANCE, description="Resultatets sorteringsordning.")
    facets: list[FacetField] = Field(
        default_factory=list,
        description="Fält vars värden och antal ska grupperas i svaret.",
    )
    return_fields: list[StoredField] = Field(
        default_factory=list,
        description="Lagrade fält att returnera; tom lista låter DigitaltMuseum returnera standarduppsättningen.",
    )

    @model_validator(mode="after")
    def validate_request(self) -> "SearchRequest":
        sources = (
            self.query,
            self.raw_query,
            self.image_url,
            self.image_base64,
            self.similar_image_id,
            self.similar_metadata_id,
        )
        if not any(value is not None for value in sources):
            raise ValueError("minst en sökkälla måste anges")
        if self.raw_query is not None and not self.raw_query.strip():
            raise ValueError("raw_query får inte vara tom")
        if any(not query.strip() for query in self.raw_filter_queries):
            raise ValueError("raw_filter_queries får inte innehålla tomma värden")
        if self.year_from is not None and self.year_to is not None and self.year_from > self.year_to:
            raise ValueError("year_from får inte vara större än year_to")
        return self

    def to_params(self) -> list[tuple[str, str]]:
        """Exportera modellen till DigitaltMuseums URL-parametrar."""
        params: list[tuple[str, str]] = [("wt", "json"), ("start", str(self.offset)), ("rows", str(self.limit))]

        if self.raw_query is not None:
            params.append(("q", self.raw_query))
        elif self.query is not None:
            key = {
                SearchMode.LEXICAL: "q",
                SearchMode.SEMANTIC_METADATA: "metadata_q",
                SearchMode.SEMANTIC_IMAGE_CONTENT: "image_content_q",
            }[self.mode]
            params.append((key, self.query))

        for term in self.terms:
            params.append(("fq", term.to_filter_query()))
        params.extend(("fq", query) for query in self.raw_filter_queries)

        if self.collection_ids:
            owners = " OR ".join(f'identifier.owner:"{escape_solr(owner)}"' for owner in self.collection_ids)
            params.append(("fq", f"({owners})"))
        if self.artifact_types:
            types = " OR ".join(f"artifact.type:{kind.value}" for kind in self.artifact_types)
            params.append(("fq", f"({types})"))
        if self.has_pictures is not None:
            params.append(("fq", f"artifact.hasPictures:{str(self.has_pictures).lower()}"))
        if self.year_from is not None:
            params.append(("fq", f"artifact.event.toYear:[{self.year_from} TO *]"))
        if self.year_to is not None:
            params.append(("fq", f"artifact.event.fromYear:[* TO {self.year_to}]"))

        for key, value in (
            ("image_url_q", str(self.image_url) if self.image_url else None),
            ("image_q", self.image_base64),
            ("similar_image_id", self.similar_image_id),
            ("similar_metadata_id", self.similar_metadata_id),
        ):
            if value is not None:
                params.append((key, value))

        if self.sort is SortOrder.PUBLISHED:
            params.append(("sort", "artifact.publishedDate desc"))
        elif self.sort is SortOrder.UPDATED:
            params.append(("sort", "artifact.updatedDate desc"))
        if self.facets:
            params.append(("facet", "true"))
            params.extend(("facet.field", facet.value) for facet in self.facets)
        if self.return_fields:
            params.append(("fl", ",".join(field.value for field in self.return_fields)))
        return params


class ArtifactRequest(BaseModel):
    """Argument till chatbotverktyget som hämtar ett fullständigt objekt."""

    model_config = ConfigDict(extra="forbid")

    unique_id: NonEmpty = Field(description="artifact.uniqueId eller artifact.uuid från en sökträff.")
    format: ArtifactFormat = Field(
        default=ArtifactFormat.SIMPLE_JSON,
        description="Önskat originalformat: simple_json, ABM eller ESE.",
    )


class CollectionsRequest(BaseModel):
    """Argument till chatbotverktyget som listar museer och samlingar."""

    model_config = ConfigDict(extra="forbid")

    countries: list[Country] = Field(
        default_factory=lambda: [Country.SWEDEN, Country.NORWAY],
        min_length=1,
        max_length=2,
        description="Länder vars publicerande museer och samlingar ska listas.",
    )


class Collection(BaseModel):
    """En post ur DigitaltMuseums ägarlista."""

    model_config = ConfigDict(extra="forbid")

    identifier: str = Field(description="DigitaltMuseums identifierare för museet eller samlingen.")
    name: str = Field(description="Museets eller samlingens publicerade namn.")
    country: Country = Field(description="Landet som ägarlistan hämtades för.")
    parent: str | None = Field(default=None, description="Eventuell överordnad ägaridentifierare.")
