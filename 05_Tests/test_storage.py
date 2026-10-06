import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "04_Implementation" / "haos" / "source" / "apps" / "mediacat_manager" / "app"))

from path_policy import FilesystemPolicy, PathPolicyError
from storage import atomic_replace_catalogue


class AtomicStorageTests(unittest.TestCase):
    def policy(self, root: Path) -> FilesystemPolicy:
        return FilesystemPolicy(root / "catalogues", root / "assets", root / "history")

    def test_atomic_replace_creates_and_replaces_catalogue(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            policy = self.policy(root)
            destination = atomic_replace_catalogue(policy, "catalogue.yaml", b"version: one\n")
            self.assertEqual(destination.read_bytes(), b"version: one\n")
            atomic_replace_catalogue(policy, "catalogue.yaml", b"version: two\n")
            self.assertEqual(destination.read_bytes(), b"version: two\n")
            self.assertEqual(list(destination.parent.glob(".*.tmp")), [])

    def test_replace_failure_preserves_existing_destination_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            policy = self.policy(root)
            destination = atomic_replace_catalogue(policy, "catalogue.yaml", b"original\n")
            with patch("storage.os.replace", side_effect=OSError("simulated")):
                with self.assertRaises(OSError):
                    atomic_replace_catalogue(policy, "catalogue.yaml", b"candidate\n")
            self.assertEqual(destination.read_bytes(), b"original\n")
            self.assertEqual(list(destination.parent.glob(".*.tmp")), [])

    def test_writer_cannot_target_asset_or_arbitrary_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            policy = self.policy(Path(temp))
            with self.assertRaises(PathPolicyError):
                atomic_replace_catalogue(policy, "../../assets/poster.yaml", b"no\n")


if __name__ == "__main__":
    unittest.main()
