import unittest

from ..clients.json_api_client import JSONApiClient


class ReleaseAssetTemplateTest(unittest.TestCase):

    def test_resolve_asset_template_01(self):
        templates = [
            (
                "Package-${version}-st${st_build}-${platform}.sublime-package",
                {
                }
            ),
        ]
        results = [
            (
                "Package-${version}-stany-any.sublime-package",
                {
                    "platforms": ["*"],
                    "sublime_text": "*",
                }
            ),
        ]
        self.assertEqual(results, JSONApiClient._expand_asset_variables(templates))

    def test_resolve_asset_template_02(self):
        templates = [
            (
                "Package-${version}-st${st_build}-${platform}.sublime-package",
                {
                    "platforms": ["*"],
                    "sublime_text": "*",
                }
            ),
        ]
        results = [
            (
                "Package-${version}-stany-any.sublime-package",
                {
                    "platforms": ["*"],
                    "sublime_text": "*",
                }
            ),
        ]
        self.assertEqual(results, JSONApiClient._expand_asset_variables(templates))

    def test_resolve_asset_template_03(self):
        templates = [
            (
                "Package-${version}-st${st_build}-py${py_version}-${platform}.sublime-package",
                {
                    "platforms": ["*"],
                    "python_versions": ["3.8"],
                    "sublime_text": "*",
                }
            ),
        ]
        results = [
            (
                "Package-${version}-stany-py38-any.sublime-package",
                {
                    "platforms": ["*"],
                    "python_versions": ["3.8"],
                    "sublime_text": "*",
                }
            ),
        ]
        self.assertEqual(results, JSONApiClient._expand_asset_variables(templates))

    def test_resolve_asset_template_04(self):
        templates = [
            (
                "Package-st${st_build}-py${py_version}-${platform}.sublime-package",
                {
                    "platforms": ["linux", "windows"],
                    "python_versions": ["3.8"],
                    "sublime_text": ">=4107",
                }
            ),
        ]
        results = [
            (
                "Package-st4107-py38-linux.sublime-package",
                {
                    "platforms": ["linux"],
                    "python_versions": ["3.8"],
                    "sublime_text": ">=4107",
                }
            ),
            (
                "Package-st4107-py38-windows.sublime-package",
                {
                    "platforms": ["windows"],
                    "python_versions": ["3.8"],
                    "sublime_text": ">=4107",
                }
            ),
        ]
        self.assertEqual(results, JSONApiClient._expand_asset_variables(templates))

    def test_resolve_asset_template_05(self):
        templates = [
            (
                "Package-st${st_build}-py${py_version}-${platform}.sublime-package",
                {
                    "platforms": ["linux", "windows"],
                    "sublime_text": "4107 - 4200",
                }
            ),
        ]
        results = [
            (
                "Package-st4107-pyany-linux.sublime-package",
                {
                    "platforms": ["linux"],
                    "sublime_text": "4107 - 4200",
                }
            ),
            (
                "Package-st4107-pyany-windows.sublime-package",
                {
                    "platforms": ["windows"],
                    "sublime_text": "4107 - 4200",
                }
            ),
        ]
        self.assertEqual(results, JSONApiClient._expand_asset_variables(templates))

    def test_resolve_asset_template_06(self):
        templates = [
            (
                "Package-st${st_build}-${platform}.sublime-package",
                {
                    "platforms": ["linux", "windows"],
                    "sublime_text": "4107 - 4200",
                }
            ),
        ]
        results = [
            (
                "Package-st4107-linux.sublime-package",
                {
                    "platforms": ["linux"],
                    "sublime_text": "4107 - 4200",
                }
            ),
            (
                "Package-st4107-windows.sublime-package",
                {
                    "platforms": ["windows"],
                    "sublime_text": "4107 - 4200",
                }
            ),
        ]
        self.assertEqual(results, JSONApiClient._expand_asset_variables(templates))
