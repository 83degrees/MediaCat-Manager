import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "04_Source" / "mediacat_manager"


class PackageTests(unittest.TestCase):
    def test_home_assistant_app_declares_ingress_and_no_host_port(self):
        config = (APP / "config.yaml").read_text(encoding="utf-8")
        self.assertIn('slug: "mediacat_manager"', config)
        self.assertIn("ingress: true", config)
        self.assertIn("ingress_port: 8099", config)
        self.assertIn("homeassistant_api: true", config)
        self.assertNotIn("ports:", config)
        self.assertNotIn("ports_description:", config)

    def test_package_uses_expected_python_app_entrypoint(self):
        dockerfile = (APP / "Dockerfile").read_text(encoding="utf-8")
        run_script = (APP / "run.sh").read_text(encoding="utf-8")
        self.assertIn('io.hass.type="app"', dockerfile)
        self.assertIn("exec python3 /app/main.py", run_script)

    def test_editor_contains_no_secret_configuration(self):
        config = (APP / "config.yaml").read_text(encoding="utf-8")
        self.assertIn("options: {}", config)
        self.assertIn("schema: {}", config)
        self.assertNotIn("password", config.lower())
        self.assertNotIn("token", config.lower())

    def test_runtime_installs_the_pinned_yaml_dependency(self):
        dockerfile = (APP / "Dockerfile").read_text(encoding="utf-8")
        requirements = (APP / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("pip3 install --no-cache-dir", dockerfile)
        self.assertEqual(requirements.strip(), "PyYAML==6.0.3")


if __name__ == "__main__":
    unittest.main()
