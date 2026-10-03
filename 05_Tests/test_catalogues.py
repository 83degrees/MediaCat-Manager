import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "04_Source" / "mediacat_manager" / "app"))

from catalogues import CatalogueError, CatalogueManager
from path_policy import FilesystemPolicy


def document(label="Test"):
    return {
        "catalogue_id": "test_catalogue",
        "catalogue_schema_version": 4,
        "items": {"one": {"type": "radio", "catalogue_label": label, "type_metadata": {"station_name": label}, "execution_methods": {}}},
        "categories": {"radio": {"category_label": "Radio", "items": ["one"]}},
    }


class FakeAdmin:
    def __init__(self, *, valid=True, reloaded=True):
        self.valid = valid
        self.reloaded = reloaded
        self.validated = []

    def capabilities(self):
        return {"admin_interface_version": 1}

    def validate(self, catalogue_yaml):
        self.validated.append(catalogue_yaml)
        return {"valid": self.valid, "catalogue_id": "test_catalogue", "errors": [] if self.valid else [{"message": "invalid"}]}

    def reload(self):
        return {"reloaded": self.reloaded, "active_catalogue_ids": ["test_catalogue"], "errors": []}


class CatalogueManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.policy = FilesystemPolicy(root / "catalogues", root / "assets", root / "history")
        self.policy.catalogue_root.mkdir()
        self.path = self.policy.catalogue_root / "storage-name.yaml"
        self.path.write_text("catalogue_id: test_catalogue\ncatalogue_schema_version: 4\nitems: {}\ncategories: {}\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_discovery_uses_internal_id_not_filename(self):
        result = CatalogueManager(self.policy, FakeAdmin()).discover()
        self.assertEqual(result["catalogues"][0]["catalogue_id"], "test_catalogue")
        self.assertEqual(result["catalogues"][0]["relative_name"], "storage-name.yaml")

    def test_invalid_candidate_is_not_written_or_snapshotted(self):
        original = self.path.read_bytes()
        result = CatalogueManager(self.policy, FakeAdmin(valid=False)).save("test_catalogue", document())
        self.assertFalse(result["saved"])
        self.assertEqual(self.path.read_bytes(), original)
        self.assertFalse(self.policy.history_root.exists())

    def test_valid_save_snapshots_atomically_and_preserves_reload_failure(self):
        manager = CatalogueManager(self.policy, FakeAdmin(reloaded=False), history_keep=2)
        result = manager.save("test_catalogue", document("Changed"))
        self.assertTrue(result["saved"])
        self.assertFalse(result["runtime_active"])
        self.assertIn("Changed", self.path.read_text(encoding="utf-8"))
        self.assertEqual(len(manager.history("test_catalogue")), 1)

    def test_history_diff_restore_and_retention(self):
        manager = CatalogueManager(self.policy, FakeAdmin(), history_keep=2)
        manager.save("test_catalogue", document("One"))
        manager.save("test_catalogue", document("Two"))
        manager.save("test_catalogue", document("Three"))
        history = manager.history("test_catalogue")
        self.assertEqual(len(history), 2)
        self.assertIn("Three", manager.diff("test_catalogue", history[0]["snapshot"])["diff"])
        result = manager.restore("test_catalogue", history[-1]["snapshot"])
        self.assertTrue(result["restored"])
        self.assertTrue(result["runtime_active"])

    def test_duplicate_internal_ids_block_selection(self):
        (self.policy.catalogue_root / "other.yml").write_text(self.path.read_text(encoding="utf-8"), encoding="utf-8")
        with self.assertRaises(CatalogueError):
            CatalogueManager(self.policy, FakeAdmin()).get("test_catalogue")

    def test_duplicate_yaml_keys_are_reported_without_rewriting(self):
        self.path.write_text(
            "catalogue_id: test_catalogue\ncatalogue_id: hidden_duplicate\nitems: {}\ncategories: {}\n",
            encoding="utf-8",
        )
        result = CatalogueManager(self.policy, FakeAdmin()).discover()
        self.assertEqual(result["catalogues"], [])
        self.assertIn("duplicate key", result["errors"][0]["message"])

    def test_timestamp_like_values_remain_strings_for_lossless_editing(self):
        self.path.write_text(
            "catalogue_id: test_catalogue\ncatalogue_schema_version: 4\nitems:\n  one:\n    release_date: 2026-10-03\ncategories: {}\n",
            encoding="utf-8",
        )
        loaded = CatalogueManager(self.policy, FakeAdmin()).get("test_catalogue")
        self.assertEqual(loaded["document"]["items"]["one"]["release_date"], "2026-10-03")


if __name__ == "__main__":
    unittest.main()
