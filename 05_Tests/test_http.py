import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "04_Source" / "mediacat_manager" / "app"))

from main import RequestHandler, build_context
from path_policy import FilesystemPolicy


CATALOGUE = b"""catalogue_id: test_catalogue
catalogue_schema_version: 4
items:
  station:
    type: radio
    catalogue_label: Test station
    type_metadata:
      station_name: Test station
    execution_methods:
      ha_mplayer:
        source:
          source_type: url
          url: https://example.com/live
          mime_type: audio/aac
categories:
  radio:
    category_label: Radio
    items: [station]
"""


class FakeAdmin:
    def capabilities(self):
        return {"admin_interface_version": 1, "current_catalogue_schema_version": 4}

    def validate(self, catalogue_yaml):
        return {"valid": True, "catalogue_id": "test_catalogue", "errors": []}

    def reload(self):
        return {"reloaded": True, "active_catalogue_ids": ["test_catalogue"], "errors": []}


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name)
        policy = FilesystemPolicy(root / "catalogues", root / "assets", root / "history")
        policy.catalogue_root.mkdir()
        policy.asset_root.mkdir()
        (policy.catalogue_root / "catalogue.yaml").write_bytes(CATALOGUE)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), RequestHandler)
        cls.server.context = build_context(policy, FakeAdmin())
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, method, path, payload=None):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=2)
        body = None if payload is None else json.dumps(payload)
        headers = {} if payload is None else {"Content-Type": "application/json"}
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        data = response.read()
        response_headers = dict(response.getheaders())
        connection.close()
        return response.status, response_headers, data

    def test_health_ingress_ui_and_security_headers_are_reachable(self):
        status, headers, body = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["status"], "ok")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        status, _, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Validate &amp; save", body)

    def test_catalogue_api_discovers_loads_and_saves(self):
        status, _, body = self.request("GET", "/api/catalogues")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["catalogues"][0]["catalogue_id"], "test_catalogue")
        status, _, body = self.request("GET", "/api/catalogues/test_catalogue")
        document = json.loads(body)["document"]
        document["items"]["station"]["catalogue_label"] = "Changed"
        status, _, body = self.request("POST", "/api/catalogues/test_catalogue/save", {"document": document})
        result = json.loads(body)
        self.assertEqual(status, 200)
        self.assertTrue(result["saved"])
        self.assertTrue(result["runtime_active"])

    def test_unknown_mutation_is_not_available(self):
        status, _, body = self.request("DELETE", "/api/catalogues/test_catalogue")
        self.assertEqual(status, 405)
        self.assertEqual(json.loads(body)["error"], "method_not_allowed")


if __name__ == "__main__":
    unittest.main()
