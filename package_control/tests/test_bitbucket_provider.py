# flake8: noqa: E121,E126,E501
import unittest

from ..http_cache import HttpCache
from ..providers.bitbucket_provider import BitBucketProvider
from ._data_decorator import data_decorator, data

from ._config import (
    BB_PASS,
    BB_USER,
    DEBUG,
    LAST_COMMIT_TIMESTAMP,
    LAST_COMMIT_VERSION,
    USER_AGENT,
)


@data_decorator
class BitBucketProviderTests(unittest.TestCase):
    maxDiff = None

    def settings(self):
        if not BB_PASS:
            self.skipTest("BitBucket app password for {} not set via env var BB_PASS".format(BB_USER))

        return {
            "debug": DEBUG,
            "cache": HttpCache(604800),
            "cache_length": 604800,
            "user_agent": USER_AGENT,
            "http_basic_auth": {
                "api.bitbucket.org": [BB_USER, BB_PASS]
            }
        }

    @data(
        (
            ("https://bitbucket.org/wbond/package_control-tester", True),
            ("https://bitbucket.org/wbond/package_control-tester/", True),
            ("https://bitbucket.org/wbond/package_control-tester/src/master", True),
            ("https://bitbucket.org/wbond", False),
            ("https://bitbucket,org/wbond/package_control-tester", False),
            ("https://github.com/wbond/package_control-tester", False),
            ("https://gitlab.com/wbond/package_control-tester", False)
        )
    )
    def match_url(self, url, result):
        self.assertEqual(result, BitBucketProvider.match_url(url))

    def test_get_libraries(self):
        provider = BitBucketProvider(
            "https://bitbucket.org/wbond/package_control-tester",
            self.settings()
        )
        self.assertEqual([], provider.get_libraries())

    def test_get_broken_libraries(self):
        provider = BitBucketProvider(
            "https://bitbucket.org/wbond/package_control-tester",
            self.settings()
        )
        self.assertEqual([], list(provider.get_broken_libraries()))

    def test_get_packages(self):
        provider = BitBucketProvider(
            "https://bitbucket.org/wbond/package_control-tester",
            self.settings()
        )
        self.assertEqual(
            [
                {
                    "name": "package_control-tester",
                    "description": "A test of Package Control upgrade messages with "
                                   "explicit versions, but date-based releases.",
                    "homepage": "https://bitbucket.org/wbond/package_control-tester",
                    "author": "wbond",
                    "readme": "https://bitbucket.org/wbond/package_control-tester/raw/master/readme.md",
                    "issues": "https://bitbucket.org/wbond/package_control-tester/issues",
                    "donate": None,
                    "source": "https://bitbucket.org/wbond/package_control-tester",
                    "labels": [],
                    "previous_names": [],
                    "releases": [
                        {
                            "date": LAST_COMMIT_TIMESTAMP,
                            "version": LAST_COMMIT_VERSION,
                            "url": "https://bitbucket.org/wbond/package_control-tester/get/master.zip",
                            "sublime_text": "*",
                            "platforms": ["*"]
                        }
                    ],
                    "last_modified": LAST_COMMIT_TIMESTAMP
                }
            ],
            provider.get_packages()
        )

    def test_get_mapped_packages(self):
        provider = BitBucketProvider(
            "https://bitbucket.org/wbond/package_control-tester",
            self.settings()
        )
        provider.settings["package_name_map"] = {"package_control-tester": "Package Control Tester"}
        self.assertEqual(
            [
                {
                    "name": "Package Control Tester",
                    "description": "A test of Package Control upgrade messages with "
                                   "explicit versions, but date-based releases.",
                    "homepage": "https://bitbucket.org/wbond/package_control-tester",
                    "author": "wbond",
                    "readme": "https://bitbucket.org/wbond/package_control-tester/raw/master/readme.md",
                    "issues": "https://bitbucket.org/wbond/package_control-tester/issues",
                    "donate": None,
                    "source": "https://bitbucket.org/wbond/package_control-tester",
                    "labels": [],
                    "previous_names": [],
                    "releases": [
                        {
                            "date": LAST_COMMIT_TIMESTAMP,
                            "version": LAST_COMMIT_VERSION,
                            "url": "https://bitbucket.org/wbond/package_control-tester/get/master.zip",
                            "sublime_text": "*",
                            "platforms": ["*"]
                        }
                    ],
                    "last_modified": LAST_COMMIT_TIMESTAMP
                }
            ],
            provider.get_packages()
        )

    def test_get_broken_packages(self):
        provider = BitBucketProvider(
            "https://bitbucket.org/wbond/package_control-tester",
            self.settings()
        )
        self.assertEqual([], list(provider.get_broken_packages()))

    def test_get_renamed_packages(self):
        provider = BitBucketProvider(
            "https://bitbucket.org/wbond/package_control-tester",
            self.settings()
        )
        self.assertEqual({}, provider.get_renamed_packages())
