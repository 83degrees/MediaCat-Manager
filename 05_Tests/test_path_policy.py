import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "04_Implementation" / "haos" / "source" / "apps" / "mediacat_manager" / "app"))

from path_policy import FilesystemPolicy, PathPolicyError


class FilesystemPolicyTests(unittest.TestCase):
    def policy(self, root: Path) -> FilesystemPolicy:
        return FilesystemPolicy(root / "catalogues", root / "assets", root / "history")

    def test_catalogue_accepts_only_yaml_beneath_catalogue_root(self):
        with tempfile.TemporaryDirectory() as temp:
            policy = self.policy(Path(temp))
            self.assertEqual(
                policy.catalogue_file("family/library.yaml"),
                (Path(temp) / "catalogues" / "family" / "library.yaml").resolve(),
            )
            with self.assertRaises(PathPolicyError):
                policy.catalogue_file("catalogue.json")

    def test_traversal_and_absolute_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            policy = self.policy(Path(temp))
            for candidate in ("../secrets.yaml", "/etc/passwd", "folder/../../escape.yaml", ""):
                with self.subTest(candidate=candidate), self.assertRaises(PathPolicyError):
                    policy.catalogue_file(candidate)

    def test_asset_boundary_is_independent_and_read_api_has_no_write_primitive(self):
        with tempfile.TemporaryDirectory() as temp:
            policy = self.policy(Path(temp))
            self.assertEqual(
                policy.asset_file("media/poster.jpg"),
                (Path(temp) / "assets" / "media" / "poster.jpg").resolve(),
            )
            self.assertFalse(hasattr(policy, "write_asset"))

    def test_history_ids_are_path_safe(self):
        with tempfile.TemporaryDirectory() as temp:
            policy = self.policy(Path(temp))
            self.assertEqual(policy.history_directory("curated_media").name, "curated_media")
            for catalogue_id in ("", "../escape", "has space", "slash/name"):
                with self.subTest(catalogue_id=catalogue_id), self.assertRaises(PathPolicyError):
                    policy.history_directory(catalogue_id)


if __name__ == "__main__":
    unittest.main()
