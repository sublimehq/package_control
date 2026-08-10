import unittest

from ..clients.bitbucket_client import BitBucketClient
from ..http_cache import HttpCache
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
class BitBucketClientTests(unittest.TestCase):
    maxDiff = None

    def settings(self, extra=None):
        if not BB_PASS:
            self.skipTest("BitBucket app password for %s not set via env var BB_PASS" % BB_USER)

        settings = {
            "debug": DEBUG,
            "cache": HttpCache(604800),
            "cache_length": 604800,
            "user_agent": USER_AGENT,
            "http_basic_auth": {
                "api.bitbucket.org": [BB_USER, BB_PASS]
            }
        }
        if extra:
            settings.update(extra)

        return settings

    @data(
        (
            (
                "1",
                "https://bitbucket.org",
                (None, None, None)
            ),
            (
                "2",
                "https://bitbucket.org/",
                (None, None, None)
            ),
            (
                "3",
                "https://bitbucket.org/packagecontrol-test",
                ("packagecontrol-test", None, None)
            ),
            (
                "4",
                "https://bitbucket.org/packagecontrol-test/",
                ("packagecontrol-test", None, None)
            ),
            (
                "5",
                "https://bitbucket.org/packagecontrol-test/package_control-tester",
                ("packagecontrol-test", "package_control-tester", None)
            ),
            (
                "6",
                "https://bitbucket.org/packagecontrol-test/package_control-tester/",
                ("packagecontrol-test", "package_control-tester", None)
            ),
            (
                "7",
                "https://bitbucket.org/packagecontrol-test/package_control-tester.git",
                ("packagecontrol-test", "package_control-tester", None)
            ),
            (
                "8",
                "https://bitbucket.org/packagecontrol-test/package_control-tester/src/master",
                ("packagecontrol-test", "package_control-tester", "master")
            ),
            (
                "9",
                "https://bitbucket.org/packagecontrol-test/package_control-tester/src/master/",
                ("packagecontrol-test", "package_control-tester", "master")
            ),
            (
                "10",
                "https://bitbucket.org/packagecontrol-test/package_control-tester/src/foo/bar",
                ("packagecontrol-test", "package_control-tester", "foo/bar")
            ),
            (
                "11",
                "https://bitbucket.org/packagecontrol-test/package_control-tester/src/foo/bar/",
                ("packagecontrol-test", "package_control-tester", "foo/bar")
            ),
            (
                "12",
                "https://bitbucket.org/packagecontrol-test/package_control-tester#tags",
                (None, None, None)
            ),
            (
                "13",
                "https://bitbucket.org/packagecontrol-test/package_control-tester/#tags",
                (None, None, None)
            ),
            (
                "14",
                "https://bitbucket;org/packagecontrol-test/package_control-tester",
                (None, None, None)
            ),
        ),
        first_param_name_suffix=True
    )
    def repo_user_branch(self, url, result):
        client = BitBucketClient(self.settings())
        self.assertEqual(result, client.user_repo_branch(url))

    def test_repo_info(self):
        client = BitBucketClient(self.settings())
        self.assertEqual(
            {
                "name": "package_control-tester",
                "description": "A test of Package Control upgrade messages with "
                               "explicit versions, but date-based releases.",
                "homepage": "https://bitbucket.org/wbond/package_control-tester",
                "author": "wbond",
                "readme": "https://bitbucket.org/wbond/package_control-tester/raw/master/readme.md",
                "issues": "https://bitbucket.org/wbond/package_control-tester/issues",
                "donate": None,
                "default_branch": "master"
            },
            client.repo_info("https://bitbucket.org/wbond/package_control-tester")
        )

    def test_user_info(self):
        client = BitBucketClient(self.settings())
        self.assertEqual(None, client.user_info("https://bitbucket.org/wbond"))

    @data(
        (
            (
                "branch_downloads",  # name
                None,  # extra_settings
                "https://bitbucket.org/wbond/package_control-tester",  # url
                None,  # tag-prefix
                [
                    {
                        "date": LAST_COMMIT_TIMESTAMP,
                        "version": LAST_COMMIT_VERSION,
                        "url": "https://bitbucket.org/wbond/package_control-tester/get/master.zip"
                    }
                ]
            ),
            (
                "tags_downloads",
                None,
                "https://bitbucket.org/wbond/package_control-tester#tags",
                None,
                [
                    {
                        "date": "2014-11-12 15:52:35",
                        "version": "1.0.1",
                        "url": "https://bitbucket.org/wbond/package_control-tester/get/1.0.1.zip"
                    },
                    {
                        "date": "2014-11-12 15:14:23",
                        "version": "1.0.1-beta",
                        "url": "https://bitbucket.org/wbond/package_control-tester/get/1.0.1-beta.zip"
                    },
                    {
                        "date": "2014-11-12 15:14:13",
                        "version": "1.0.0",
                        "url": "https://bitbucket.org/wbond/package_control-tester/get/1.0.0.zip"
                    },
                    {
                        "date": "2014-11-12 02:02:22",
                        "version": "0.9.0",
                        "url": "https://bitbucket.org/wbond/package_control-tester/get/0.9.0.zip"
                    }
                ]
            ),
            (
                "tags_limited_downloads",
                {"max_releases": 1},
                "https://bitbucket.org/wbond/package_control-tester#tags",
                None,
                [
                    {
                        "date": "2014-11-12 15:52:35",
                        "version": "1.0.1",
                        "url": "https://bitbucket.org/wbond/package_control-tester/get/1.0.1.zip"
                    }
                ]
            ),
            (
                "tags_with_prefix_downloads",
                None,
                "https://bitbucket.org/wbond/package_control-tester#tags",
                "win-",
                [
                    {
                        "date": "2014-11-28 20:54:15",
                        "version": "1.0.2",
                        "url": "https://bitbucket.org/wbond/package_control-tester/get/win-1.0.2.zip"
                    }
                ]
            ),
        ),
        first_param_name_suffix=True
    )
    def download_info(self, extra_settings, url, tag_prefix, result):
        client = BitBucketClient(self.settings(extra_settings))
        self.assertEqual(result, client.download_info(url, tag_prefix))

    @data(
        (
            (
                "via_repo_url",  # name
                None,  # extra_settings
                "https://bitbucket.org/wbond/package_control-tester",  # url
                None,  # tag-prefix
                [
                    {
                        "date": LAST_COMMIT_TIMESTAMP,
                        "version": LAST_COMMIT_VERSION,
                        "url": "https://bitbucket.org/wbond/package_control-tester/get/master.zip"
                    }
                ]
            ),
        ),
        first_param_name_suffix=True
    )
    def download_info_from_branch(self, extra_settings, url, branch, result):
        client = BitBucketClient(self.settings(extra_settings))
        self.assertEqual(result, client.download_info_from_branch(url, branch))

    @data(
        (
            (
                "via_repo_url",
                None,
                "https://bitbucket.org/wbond/package_control-tester",
                None,
                [
                    {
                        "date": "2014-11-12 15:52:35",
                        "version": "1.0.1",
                        "url": "https://bitbucket.org/wbond/package_control-tester/get/1.0.1.zip"
                    },
                    {
                        "date": "2014-11-12 15:14:23",
                        "version": "1.0.1-beta",
                        "url": "https://bitbucket.org/wbond/package_control-tester/get/1.0.1-beta.zip"
                    },
                    {
                        "date": "2014-11-12 15:14:13",
                        "version": "1.0.0",
                        "url": "https://bitbucket.org/wbond/package_control-tester/get/1.0.0.zip"
                    },
                    {
                        "date": "2014-11-12 02:02:22",
                        "version": "0.9.0",
                        "url": "https://bitbucket.org/wbond/package_control-tester/get/0.9.0.zip"
                    }
                ]
            ),
            (
                "via_repo_url_limited",
                {"max_releases": 1},
                "https://bitbucket.org/wbond/package_control-tester",
                None,
                [
                    {
                        "date": "2014-11-12 15:52:35",
                        "version": "1.0.1",
                        "url": "https://bitbucket.org/wbond/package_control-tester/get/1.0.1.zip"
                    }
                ]
            ),
            (
                "via_repo_url_with_prefix",
                None,
                "https://bitbucket.org/wbond/package_control-tester",
                "win-",
                [
                    {
                        "date": "2014-11-28 20:54:15",
                        "version": "1.0.2",
                        "url": "https://bitbucket.org/wbond/package_control-tester/get/win-1.0.2.zip"
                    }
                ]
            ),
        ),
        first_param_name_suffix=True
    )
    def download_info_from_tags(self, extra_settings, url, tag_prefix, result):
        client = BitBucketClient(self.settings(extra_settings))
        self.assertEqual(result, client.download_info_from_tags(url, tag_prefix))

    @data(
        (
            (
                # url
                "https://bitbucket.org/wbond/package_control-tester",
                # asset_templates
                [
                    # asset name pattern, { selectors }
                    ("package_control-tester.sublime-package", {}),
                ],
                # tag prefix
                None,
                # results (note: not supported by BitBucket Client)
                None,
            ),
        )
    )
    def download_info_from_releases(self, url, asset_templates, tag_prefix, result):
        client = BitBucketClient(self.settings())
        self.assertEqual(result, client.download_info_from_releases(url, asset_templates, tag_prefix))
