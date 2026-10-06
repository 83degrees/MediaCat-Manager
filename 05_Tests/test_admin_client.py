import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "04_Implementation" / "haos" / "source" / "apps" / "mediacat_manager" / "app"))

from admin_client import AdminClientError, MediaCatAdminClient


class StubClient(MediaCatAdminClient):
    def __init__(self, response):
        super().__init__(token="test")
        self.response = response

    def _call(self, service, data):
        return self.response


def supported(**updates):
    response = {
        "admin_interface_version": 1,
        "catalogue_directory": "mediacat/catalogues",
        "supported_catalogue_schema_versions": [4],
        "validation_supported": True,
        "transactional_reload_supported": True,
    }
    response.update(updates)
    return response


class AdminClientTests(unittest.TestCase):
    def test_supported_contract_is_accepted(self):
        self.assertEqual(StubClient(supported()).capabilities()["admin_interface_version"], 1)

    def test_incompatible_contract_version_directory_or_schema_fails_closed(self):
        cases = (
            supported(admin_interface_version=2),
            supported(catalogue_directory="other/path"),
            supported(supported_catalogue_schema_versions=[5]),
            supported(validation_supported=False),
        )
        for response in cases:
            with self.subTest(response=response), self.assertRaises(AdminClientError):
                StubClient(response).capabilities()


if __name__ == "__main__":
    unittest.main()
