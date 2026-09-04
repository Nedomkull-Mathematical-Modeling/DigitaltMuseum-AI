import os
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from dimu import DimuClient
from dimu.api import create_app, openai_tools


AUTH = {"Authorization": "Bearer service-secret"}


class ApiTest(unittest.TestCase):
    def make_client(self, handler):
        dimu = DimuClient("upstream-secret", base_url="https://upstream.test", transport=httpx.MockTransport(handler))
        return dimu, TestClient(create_app(client=dimu, service_token="service-secret"))

    def test_search_body_is_forwarded_without_json_reserialization(self):
        body = '{ "response" : { "docs" : [{"ok":true,"unicode":"åäö","future":null}] } }'.encode()
        dimu, client = self.make_client(
            lambda request: httpx.Response(200, content=body, headers={"content-type": "application/json; charset=utf-8"})
        )
        try:
            with client:
                response = client.post("/v1/search", headers=AUTH, json={"query": "museum"})
            self.assertEqual(response.content, body)
            self.assertEqual(response.headers["content-type"], "application/json; charset=utf-8")
        finally:
            dimu.close()

    def test_raw_collection_xml_is_forwarded_unchanged(self):
        body = '<?xml version="1.0"?><owners><owner><name>Ö</name></owner></owners>'.encode()
        dimu, client = self.make_client(
            lambda request: httpx.Response(200, content=body, headers={"content-type": "application/xml"})
        )
        try:
            with client:
                response = client.get("/v1/collections/se/raw", headers=AUTH)
            self.assertEqual(response.content, body)
        finally:
            dimu.close()

    def test_collection_list_combines_countries(self):
        def handler(request: httpx.Request) -> httpx.Response:
            country = request.url.params["country"]
            return httpx.Response(
                200,
                content=f"<owners><owner><identifier>{country}-1</identifier><name>{country}</name></owner></owners>".encode(),
            )

        dimu, client = self.make_client(handler)
        try:
            with client:
                response = client.get("/v1/collections", headers=AUTH)
            self.assertEqual(response.status_code, 200)
            self.assertEqual([item["country"] for item in response.json()], ["se", "no"])
        finally:
            dimu.close()

    def test_artifact_format_is_forwarded(self):
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.params["mapping"], "ESE")
            return httpx.Response(200, content=b"<record />", headers={"content-type": "application/xml"})

        dimu, client = self.make_client(handler)
        try:
            with client:
                response = client.get("/v1/artifacts/123?format=ESE", headers=AUTH)
            self.assertEqual(response.content, b"<record />")
        finally:
            dimu.close()

    def test_authentication_and_validation(self):
        dimu, client = self.make_client(lambda request: httpx.Response(200, content=b"{}"))
        try:
            with client:
                self.assertEqual(client.get("/health").status_code, 401)
                self.assertEqual(client.get("/health", headers=AUTH).json(), {"status": "ok"})
                response = client.post("/v1/search", headers=AUTH, json={"query": "x", "limit": 21})
                self.assertEqual(response.status_code, 422)
        finally:
            dimu.close()

    def test_startup_defaults_to_demo_with_warning(self):
        with patch.dict(os.environ):
            os.environ.pop("DIMU_API_KEY", None)
            with self.assertWarnsRegex(RuntimeWarning, "demo-nyckel"):
                with TestClient(create_app(service_token="service-secret")) as client:
                    self.assertEqual(client.get("/health", headers=AUTH).status_code, 200)

    def test_timeout_and_upstream_errors_are_sanitized(self):
        def timeout(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("contains secret", request=request)

        dimu, client = self.make_client(timeout)
        try:
            with client:
                response = client.post("/v1/search", headers=AUTH, json={"query": "x"})
            self.assertEqual(response.status_code, 504)
            self.assertNotIn("secret", response.text)
        finally:
            dimu.close()

        dimu, client = self.make_client(lambda request: httpx.Response(500, content=b"private upstream body"))
        try:
            with client:
                response = client.post("/v1/search", headers=AUTH, json={"raw_query": "private query"})
            self.assertEqual(response.status_code, 502)
            self.assertNotIn("private", response.text)
        finally:
            dimu.close()


class OpenAIToolSchemaTest(unittest.TestCase):
    def test_tools_are_strict_and_closed_recursively(self):
        tools = openai_tools()
        self.assertEqual(len(tools), 3)

        def inspect(value):
            if isinstance(value, dict):
                if "properties" in value:
                    self.assertFalse(value["additionalProperties"])
                    self.assertEqual(set(value["required"]), set(value["properties"]))
                    for property_schema in value["properties"].values():
                        self.assertIn("description", property_schema)
                for child in value.values():
                    inspect(child)
            elif isinstance(value, list):
                for child in value:
                    inspect(child)

        for tool in tools:
            self.assertTrue(tool["strict"])
            self.assertTrue(tool["description"])
            inspect(tool["parameters"])


if __name__ == "__main__":
    unittest.main()
