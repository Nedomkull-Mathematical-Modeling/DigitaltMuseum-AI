import json
import unittest
from unittest.mock import patch

import httpx
from pydantic import ValidationError

from dimu import (
    ArtifactFormat,
    ArtifactType,
    DimuClient,
    FacetField,
    MatchMode,
    Occurrence,
    SearchField,
    SearchMode,
    SearchRequest,
    SearchTerm,
    SortOrder,
    StoredField,
)


class SearchRequestTest(unittest.TestCase):
    def test_exports_structured_filters_and_repeated_parameters(self):
        request = SearchRequest(
            query="Uppsala slott",
            collection_ids=["S-UM", "S-AM"],
            artifact_types=[ArtifactType.PHOTOGRAPH, ArtifactType.THING],
            terms=[
                SearchTerm(
                    field=SearchField.EVENT_PLACE,
                    value='Uppsala: centrum?',
                    match=MatchMode.PHRASE,
                ),
                SearchTerm(
                    field=SearchField.MATERIAL,
                    value="plast",
                    occurrence=Occurrence.MUST_NOT,
                ),
            ],
            raw_filter_queries=["artifact.technique:(foto OR fotografi)"],
            has_pictures=True,
            year_from=1900,
            year_to=1950,
            sort=SortOrder.UPDATED,
            facets=[FacetField.COLLECTION, FacetField.TYPE],
            return_fields=[StoredField.UNIQUE_ID, StoredField.TITLE],
            offset=20,
            limit=20,
        )
        params = request.to_params()

        self.assertIn(("q", "Uppsala slott"), params)
        self.assertIn(("fq", 'artifact.event.place:"Uppsala\\: centrum\\?"'), params)
        self.assertIn(("fq", "-artifact.material:(plast)"), params)
        self.assertIn(("fq", "artifact.technique:(foto OR fotografi)"), params)
        self.assertIn(("fq", '(identifier.owner:"S\\-UM" OR identifier.owner:"S\\-AM")'), params)
        self.assertIn(("fq", "(artifact.type:Photograph OR artifact.type:Thing)"), params)
        self.assertIn(("fq", "artifact.hasPictures:true"), params)
        self.assertIn(("fq", "artifact.event.toYear:[1900 TO *]"), params)
        self.assertIn(("fq", "artifact.event.fromYear:[* TO 1950]"), params)
        self.assertIn(("sort", "artifact.updatedDate desc"), params)
        self.assertEqual([value for key, value in params if key == "facet.field"], ["identifier.owner", "artifact.type"])
        self.assertIn(("fl", "artifact.uniqueId,artifact.ingress.title"), params)
        self.assertIn(("start", "20"), params)
        self.assertIn(("rows", "20"), params)

    def test_maps_all_text_search_modes(self):
        expected = {
            SearchMode.LEXICAL: "q",
            SearchMode.SEMANTIC_METADATA: "metadata_q",
            SearchMode.SEMANTIC_IMAGE_CONTENT: "image_content_q",
        }
        for mode, key in expected.items():
            with self.subTest(mode=mode):
                self.assertIn((key, "hästar i snö"), SearchRequest(query="hästar i snö", mode=mode).to_params())

    def test_raw_query_wins_and_raw_filters_are_verbatim(self):
        request = SearchRequest(
            query="ignoreras",
            raw_query=' artifact.title:("A+B" OR slott) ',
            raw_filter_queries=[" -artifact.material:trä "],
        )
        params = request.to_params()
        self.assertIn(("q", ' artifact.title:("A+B" OR slott) '), params)
        self.assertNotIn(("q", "ignoreras"), params)
        self.assertIn(("fq", " -artifact.material:trä "), params)

    def test_exports_image_and_similarity_searches(self):
        params = SearchRequest(
            image_url="https://example.org/bild.jpg",
            image_base64="YWJj",
            similar_image_id="image-uuid",
            similar_metadata_id="metadata-uuid",
        ).to_params()
        self.assertIn(("image_url_q", "https://example.org/bild.jpg"), params)
        self.assertIn(("image_q", "YWJj"), params)
        self.assertIn(("similar_image_id", "image-uuid"), params)
        self.assertIn(("similar_metadata_id", "metadata-uuid"), params)

    def test_validates_request_boundaries(self):
        invalid = (
            {},
            {"query": "x", "limit": 21},
            {"query": "x", "year_from": 2000, "year_to": 1900},
            {"query": "x", "collection_ids": [str(i) for i in range(51)]},
            {"raw_query": "   "},
            {"query": "x", "raw_filter_queries": ["   "]},
            {"query": "x", "unexpected": True},
        )
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValidationError):
                SearchRequest.model_validate(values)


class DimuClientTest(unittest.TestCase):
    def test_defaults_to_demo_and_warns(self):
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.params["api.key"], "demo")
            return httpx.Response(200, content=b"{}")

        with patch.dict("os.environ", {}, clear=True):
            with self.assertWarnsRegex(RuntimeWarning, "demo-nyckel"):
                with DimuClient(base_url="https://example.test", transport=httpx.MockTransport(handler)) as client:
                    client.search(SearchRequest(query="museum"))

    def test_returns_unparsed_search_response_and_preserves_repeated_params(self):
        body = '{"ok":true,"unknown":{"unicode":"räksmörgås","nothing":null}}'.encode()

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.params.get_list("fq"), ["one", "two"])
            self.assertEqual(request.url.params["api.key"], "secret")
            return httpx.Response(200, content=body, headers={"content-type": "application/json"})

        with DimuClient("secret", base_url="https://example.test", transport=httpx.MockTransport(handler)) as client:
            response = client.search(SearchRequest(raw_query="*:*", raw_filter_queries=["one", "two"]))

        self.assertEqual(response.content, body)

    def test_artifact_supports_every_documented_format(self):
        seen = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.url.params["mapping"])
            return httpx.Response(200, content=b"record")

        with DimuClient("secret", base_url="https://example.test", transport=httpx.MockTransport(handler)) as client:
            for mapping in ArtifactFormat:
                self.assertEqual(client.artifact("id", mapping).content, b"record")

        self.assertEqual(seen, ["simple_json", "ABM", "ESE"])

    def test_collections_parses_the_owner_shape(self):
        xml = b"<owners><owner><identifier>S-X</identifier><parent>S-P</parent><name>Museum</name></owner></owners>"
        transport = httpx.MockTransport(lambda request: httpx.Response(200, content=xml))
        with DimuClient("secret", base_url="https://example.test", transport=transport) as client:
            collections = client.collections("se")
        self.assertEqual(collections[0].model_dump(mode="json"), {
            "identifier": "S-X", "name": "Museum", "country": "se", "parent": "S-P"
        })


if __name__ == "__main__":
    unittest.main()
