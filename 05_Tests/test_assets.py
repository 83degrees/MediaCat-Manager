import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "04_Implementation" / "haos" / "source" / "apps" / "mediacat_manager" / "app"))

from assets import AssetBrowser
from path_policy import FilesystemPolicy, PathPolicyError


class AssetBrowserTests(unittest.TestCase):
    def test_only_images_are_listed_and_no_write_surface_exists(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            policy = FilesystemPolicy(root / "catalogues", root / "assets", root / "history")
            folder = policy.asset_root / "images"
            folder.mkdir(parents=True)
            (folder / "poster.png").write_bytes(b"png")
            (folder / "secret.txt").write_text("no", encoding="utf-8")
            browser = AssetBrowser(policy)
            result = browser.list("images")
            self.assertEqual([entry["name"] for entry in result["entries"]], ["poster.png"])
            self.assertFalse(hasattr(browser, "write"))

    def test_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            policy = FilesystemPolicy(root / "catalogues", root / "assets", root / "history")
            policy.asset_root.mkdir()
            with self.assertRaises(PathPolicyError):
                AssetBrowser(policy).list("../catalogues")


if __name__ == "__main__":
    unittest.main()
