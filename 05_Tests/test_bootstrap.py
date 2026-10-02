import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "04_Source" / "mediacat_manager" / "app"))

from main import RequestHandler


class BootstrapHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), RequestHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method: str, path: str):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=2)
        connection.request(method, path)
        response = connection.getresponse()
        body = response.read()
        headers = dict(response.getheaders())
        connection.close()
        return response.status, headers, body

    def test_health_and_ingress_shell_are_reachable(self):
        status, headers, body = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["status"], "ok")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")

        status, _, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Bootstrap ready", body)
        self.assertIn(b"ASTV-286", body)

    def test_bootstrap_metadata_preserves_scope_boundary(self):
        status, _, body = self.request("GET", "/api/bootstrap")
        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertFalse(payload["editor_available"])
        self.assertEqual(payload["mediacat_admin_interface"], 1)
        self.assertEqual(payload["boundaries"]["assets_access"], "read-only")

    def test_mutating_http_methods_are_rejected(self):
        status, _, body = self.request("POST", "/api/catalogues")
        self.assertEqual(status, 405)
        self.assertEqual(json.loads(body)["error"], "bootstrap_is_read_only")


if __name__ == "__main__":
    unittest.main()
