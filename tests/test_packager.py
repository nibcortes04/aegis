import unittest
import os
import sys
import json
import tempfile
import shutil
import hashlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
import package_plugin

class TestPluginPackager(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.temp_dir = tempfile.mkdtemp(prefix="aegis_pkg_test_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_manifest_success(self):
        manifest = package_plugin.validate_manifest(self.repo_root)
        self.assertEqual(manifest["name"], "aegis")
        self.assertTrue(manifest["version"].startswith("1."))
        self.assertIn("author", manifest)
        self.assertIn("license", manifest)

    def test_validate_manifest_missing_field(self):
        bad_manifest_dir = os.path.join(self.temp_dir, "bad_manifest")
        os.makedirs(bad_manifest_dir, exist_ok=True)
        bad_json = os.path.join(bad_manifest_dir, "plugin.json")
        with open(bad_json, "w", encoding="utf-8") as f:
            json.dump({"name": "aegis"}, f)
        
        with self.assertRaises(ValueError) as ctx:
            package_plugin.validate_manifest(bad_manifest_dir)
        self.assertIn("Campo obligatorio", str(ctx.exception))

    def test_validate_manifest_invalid_semver(self):
        bad_manifest_dir = os.path.join(self.temp_dir, "bad_semver")
        os.makedirs(bad_manifest_dir, exist_ok=True)
        bad_json = os.path.join(bad_manifest_dir, "plugin.json")
        with open(bad_json, "w", encoding="utf-8") as f:
            json.dump({
                "name": "aegis",
                "version": "v-invalid-1",
                "description": "test",
                "author": {"name": "test"},
                "license": "MIT"
            }, f)
        
        with self.assertRaises(ValueError) as ctx:
            package_plugin.validate_manifest(bad_manifest_dir)
        self.assertIn("SemVer", str(ctx.exception))

    def test_validate_essential_files(self):
        self.assertTrue(package_plugin.validate_essential_files(self.repo_root))

    def test_exclusion_rules(self):
        self.assertTrue(package_plugin.should_exclude(".git/config"))
        self.assertTrue(package_plugin.should_exclude(".github/workflows/ci.yml"))
        self.assertTrue(package_plugin.should_exclude("tests/test_packager.py"))
        self.assertTrue(package_plugin.should_exclude("docs/index.html"))
        self.assertTrue(package_plugin.should_exclude("scripts/__pycache__/something.pyc"))
        self.assertTrue(package_plugin.should_exclude(".env.local"))
        self.assertTrue(package_plugin.should_exclude(".DS_Store"))

        # Archivos que SÍ deben incluirse
        self.assertFalse(package_plugin.should_exclude("plugin.json"))
        self.assertFalse(package_plugin.should_exclude("scripts/agy_hook_handler.py"))
        self.assertFalse(package_plugin.should_exclude("skills/aegis/SKILL.md"))
        self.assertFalse(package_plugin.should_exclude("mcp/mcp_server.py"))

    def test_compute_sha256(self):
        test_file = os.path.join(self.temp_dir, "sample.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("hello aegis")
        expected_hash = hashlib.sha256(b"hello aegis").hexdigest()
        self.assertEqual(package_plugin.compute_sha256(test_file), expected_hash)

    def test_package_plugin_dry_run(self):
        res = package_plugin.package_plugin(self.repo_root, self.temp_dir, dry_run=True)
        self.assertTrue(res.get("dry_run"))
        self.assertGreater(res.get("files_count", 0), 20)
        # En dry-run no deben existir los archivos .tar.gz
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir, "aegis-v1.5.0.tar.gz")))

    def test_package_plugin_end_to_end(self):
        out_dir = os.path.join(self.temp_dir, "dist")
        res = package_plugin.package_plugin(self.repo_root, out_dir, verify=True)

        self.assertTrue(os.path.isfile(res["tarball"]))
        self.assertTrue(os.path.isfile(res["zip"]))
        self.assertTrue(os.path.isfile(res["checksums"]))

        with open(res["checksums"], "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("aegis-v", content)
            self.assertIn(".tar.gz", content)
            self.assertIn(".zip", content)

if __name__ == "__main__":
    unittest.main()
