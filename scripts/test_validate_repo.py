import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import validate_repo


class TestDeployableDependencies(unittest.TestCase):
    def run_validator(self, dependencies):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for module, depends in dependencies.items():
                module_path = root / module
                module_path.mkdir()
                (module_path / "__manifest__.py").write_text(
                    repr({"version": "1.0", "depends": depends})
                )

            with patch.object(validate_repo, "ROOT", root):
                return validate_repo.main()

    def test_rejects_direct_enterprise_dependency(self):
        dependencies = {
            "l10n_ve_contact": [],
            "l10n_ve_sale": ["web_enterprise"],
            "l10n_ve_stock": [],
        }
        with self.assertRaisesRegex(
            SystemExit, "l10n_ve_sale -> web_enterprise"
        ):
            self.run_validator(dependencies)

    def test_rejects_transitive_enterprise_dependency(self):
        dependencies = {
            "l10n_ve_contact": [],
            "l10n_ve_sale": ["community_bridge"],
            "l10n_ve_stock": [],
            "community_bridge": ["web_enterprise"],
        }
        with self.assertRaisesRegex(
            SystemExit,
            "l10n_ve_sale -> community_bridge -> web_enterprise",
        ):
            self.run_validator(dependencies)

    def test_ignores_optional_enterprise_dependent_module(self):
        dependencies = {
            "l10n_ve_contact": [],
            "l10n_ve_sale": [],
            "l10n_ve_stock": [],
            "l10n_ve_optional": ["web_enterprise"],
        }
        self.assertEqual(self.run_validator(dependencies), 0)

    def test_allows_external_community_dependency(self):
        dependencies = {
            "l10n_ve_contact": ["base"],
            "l10n_ve_sale": [],
            "l10n_ve_stock": [],
        }
        self.assertEqual(self.run_validator(dependencies), 0)

    def test_allows_cycles_and_duplicate_traversal(self):
        dependencies = {
            "l10n_ve_contact": [],
            "l10n_ve_sale": ["community_bridge", "community_bridge"],
            "l10n_ve_stock": [],
            "community_bridge": ["l10n_ve_sale"],
        }
        self.assertEqual(self.run_validator(dependencies), 0)

    def test_rejects_malformed_dependencies(self):
        dependencies = {
            "l10n_ve_contact": "web_enterprise",
            "l10n_ve_sale": [],
            "l10n_ve_stock": [],
        }
        with self.assertRaisesRegex(SystemExit, "l10n_ve_contact"):
            self.run_validator(dependencies)

    def test_rejects_missing_local_dependency(self):
        dependencies = {
            "l10n_ve_contact": [],
            "l10n_ve_sale": [],
            "l10n_ve_stock": ["l10n_ve_missing"],
        }
        with self.assertRaisesRegex(
            SystemExit, "l10n_ve_stock -> l10n_ve_missing"
        ):
            self.run_validator(dependencies)


if __name__ == "__main__":
    unittest.main()
