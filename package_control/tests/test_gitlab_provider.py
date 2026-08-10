# flake8: noqa: E121,E126,E501
import unittest

from ..http_cache import HttpCache
from ..providers.gitlab_provider import GitLabProvider
from ._data_decorator import data_decorator, data

from ._config import (
    DEBUG,
    GL_PASS,
    GL_USER,
    USER_AGENT,
)


@data_decorator
class GitLabProviderTests(unittest.TestCase):
    maxDiff = None

    def settings(self):
        if not GL_PASS:
            self.skipTest("GitLab personal access token for %s not set via env var GL_PASS" % GL_USER)

        return {
            "debug": DEBUG,
            "cache": HttpCache(604800),
            "cache_length": 604800,
            "user_agent": USER_AGENT,
            "http_basic_auth": {
                "gitlab.com": [GL_USER, GL_PASS]
            }
        }

    @data(
        (
            ("https://gitlab.com/packagecontrol-test/package_control-tester", True),
            ("https://gitlab.com/packagecontrol-test/package_control-tester/", True),
            ("https://gitlab.com/packagecontrol-test/package_control-tester/-/tree/master", True),
            ("https://gitlab.com/packagecontrol-test", False),
            ("https://gitlab,com/packagecontrol-test/package_control-tester", False),
            ("https://github.com/packagecontrol-test/package_control-tester", False),
            ("https://bitbucket.org/wbond/package_control-tester", False)
        )
    )
    def match_url(self, url, result):
        self.assertEqual(result, GitLabProvider.match_url(url))

    def test_get_libraries(self):
        provider = GitLabProvider(
            "https://gitlab.com/packagecontrol-test/package_control-tester",
            self.settings()
        )
        self.assertEqual([], list(provider.get_libraries()))

    def test_get_broken_libraries(self):
        provider = GitLabProvider(
            "https://gitlab.com/packagecontrol-test/package_control-tester",
            self.settings()
        )
        self.assertEqual([], list(provider.get_broken_libraries()))

    def test_get_packages(self):
        provider = GitLabProvider(
            "https://gitlab.com/packagecontrol-test/package_control-tester",
            self.settings()
        )
        self.assertEqual(
            [
                {
                    "name": "package_control-tester",
                    "description": "A test of Package Control upgrade messages with "
                                   "explicit versions, but date-based releases.",
                    "homepage": "https://gitlab.com/packagecontrol-test/package_control-tester",
                    "author": "packagecontrol-test",
                    "readme": "https://gitlab.com/packagecontrol-test/"
                              "package_control-tester/-/raw/master/readme.md",
                    "issues": None,
                    "donate": None,
                    "buy": None,
                    "sources": ["https://gitlab.com/packagecontrol-test/package_control-tester"],
                    "labels": [],
                    "previous_names": [],
                    "releases": [
                        {
                            "date": "2020-07-15 10:50:38",
                            "version": "2020.07.15.10.50.38",
                            "url": "https://gitlab.com/packagecontrol-test/"
                                   "package_control-tester/-/archive/master/"
                                   "package_control-tester-master.zip",
                            "sublime_text": "*",
                            "platforms": ["*"]
                        }
                    ],
                    "last_modified": "2020-07-15 10:50:38"
                }
            ],
            list(provider.get_packages())
        )

    def test_get_broken_packages(self):
        provider = GitLabProvider(
            "https://gitlab.com/packagecontrol-test/package_control-tester",
            self.settings()
        )
        self.assertEqual([], list(provider.get_broken_packages()))

    def test_get_renamed_packages(self):
        provider = GitLabProvider(
            "https://gitlab.com/packagecontrol-test/package_control-tester",
            self.settings()
        )
        self.assertEqual({}, provider.get_renamed_packages())

    def test_get_sources(self):
        provider = GitLabProvider(
            "https://gitlab.com/packagecontrol-test/package_control-tester",
            self.settings()
        )
        self.assertEqual(
            ["https://gitlab.com/packagecontrol-test/package_control-tester"],
            provider.get_sources()
        )
