# flake8: noqa: E121,E126,E501
import unittest

from ..http_cache import HttpCache
from ..providers.github_provider import GitHubProvider
from ._data_decorator import data_decorator, data

from ._config import (
    DEBUG,
    GH_PASS,
    GH_USER,
    LAST_COMMIT_TIMESTAMP,
    LAST_COMMIT_VERSION,
    USER_AGENT,
)


@data_decorator
class GitHubProviderTests(unittest.TestCase):
    maxDiff = None

    def settings(self):
        if not GH_PASS:
            self.skipTest("GitHub personal access token for %s not set via env var GH_PASS" % GH_USER)

        return {
            "debug": DEBUG,
            "cache": HttpCache(604800),
            "cache_length": 604800,
            "user_agent": USER_AGENT,
            "http_basic_auth": {
                "api.github.com": [GH_USER, GH_PASS],
                "raw.githubusercontent.com": [GH_USER, GH_PASS],
            }
        }

    @data(
        (
            ("https://github.com/packagecontrol-test/package_control-tester", True),
            ("https://github.com/packagecontrol-test/package_control-tester/", True),
            ("https://github.com/packagecontrol-test/package_control-tester/tree/master", True),
            ("https://github.com/packagecontrol-test", False),
            ("https://github,com/packagecontrol-test/package_control-tester", False),
            ("https://gitlab.com/packagecontrol-test/package_control-tester", False),
            ("https://bitbucket.org/wbond/package_control-tester", False)
        )
    )
    def match_url(self, url, result):
        self.assertEqual(result, GitHubProvider.match_url(url))

    def test_get_libraries(self):
        provider = GitHubProvider(
            "https://github.com/packagecontrol-test/package_control-tester",
            self.settings()
        )
        self.assertEqual([], list(provider.get_libraries()))

    def test_get_broken_libraries(self):
        provider = GitHubProvider(
            "https://github.com/packagecontrol-test/package_control-tester",
            self.settings()
        )
        self.assertEqual([], list(provider.get_broken_libraries()))

    def test_get_packages(self):
        provider = GitHubProvider(
            "https://github.com/packagecontrol-test/package_control-tester",
            self.settings()
        )
        self.assertEqual(
            [
               {
                    "name": "package_control-tester",
                    "description": "A test of Package Control upgrade messages with "
                                   "explicit versions, but date-based releases.",
                    "homepage": "https://github.com/packagecontrol-test/package_control-tester",
                    "author": "packagecontrol-test",
                    "readme": "https://raw.githubusercontent.com/packagecontrol-test"
                              "/package_control-tester/master/readme.md",
                    "issues": "https://github.com/packagecontrol-test/package_control-tester/issues",
                    "donate": None,
                    "buy": None,
                    "sources": ["https://github.com/packagecontrol-test/package_control-tester"],
                    "labels": [],
                    "previous_names": [],
                    "releases": [
                        {
                            "date": LAST_COMMIT_TIMESTAMP,
                            "version": LAST_COMMIT_VERSION,
                            "url": "https://codeload.github.com/packagecontrol-test"
                                   "/package_control-tester/zip/master",
                            "sublime_text": "*",
                            "platforms": ["*"]
                        }
                    ],
                    "last_modified": LAST_COMMIT_TIMESTAMP
                }
            ],
            list(provider.get_packages())
        )

    def test_get_broken_packages(self):
        provider = GitHubProvider(
            "https://github.com/packagecontrol-test/package_control-tester",
            self.settings()
        )
        self.assertEqual([], list(provider.get_broken_packages()))

    def test_get_renamed_packages(self):
        provider = GitHubProvider(
            "https://github.com/packagecontrol-test/package_control-tester",
            self.settings()
        )
        self.assertEqual({}, provider.get_renamed_packages())

    def test_get_sources(self):
        provider = GitHubProvider(
            "https://github.com/packagecontrol-test/package_control-tester",
            self.settings()
        )
        self.assertEqual(
            ["https://github.com/packagecontrol-test/package_control-tester"],
            provider.get_sources()
        )
