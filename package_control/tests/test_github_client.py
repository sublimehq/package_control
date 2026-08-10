import unittest

from ..clients.github_client import GitHubClient
from ..http_cache import HttpCache
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
class GitHubClientTests(unittest.TestCase):
    maxDiff = None

    def settings(self, extra=None):
        if not GH_PASS:
            self.skipTest("GitHub personal access token for %s not set via env var GH_PASS" % GH_USER)

        settings = {
            "debug": DEBUG,
            "cache": HttpCache(604800),
            "cache_length": 604800,
            "user_agent": USER_AGENT,
            "http_basic_auth": {
                "api.github.com": [GH_USER, GH_PASS],
                "raw.githubusercontent.com": [GH_USER, GH_PASS],
            }
        }
        if extra:
            settings.update(extra)

        return settings

    @data(
        (
            (
                "1",
                "https://github.com",
                (None, None, None)
            ),
            (
                "2",
                "https://github.com/",
                (None, None, None)
            ),
            (
                "3",
                "https://github.com/packagecontrol-test",
                ("packagecontrol-test", None, None)
            ),
            (
                "4",
                "https://github.com/packagecontrol-test/",
                ("packagecontrol-test", None, None)
            ),
            (
                "5",
                "https://github.com/packagecontrol-test/package_control-tester",
                ("packagecontrol-test", "package_control-tester", None)
            ),
            (
                "6",
                "https://github.com/packagecontrol-test/package_control-tester/",
                ("packagecontrol-test", "package_control-tester", None)
            ),
            (
                "7",
                "https://github.com/packagecontrol-test/package_control-tester.git",
                ("packagecontrol-test", "package_control-tester", None)
            ),
            (
                "8",
                "https://github.com/packagecontrol-test/package_control-tester/tree/master",
                ("packagecontrol-test", "package_control-tester", "master")
            ),
            (
                "9",
                "https://github.com/packagecontrol-test/package_control-tester/tree/master/",
                ("packagecontrol-test", "package_control-tester", "master")
            ),
            (
                "10",
                "https://github.com/packagecontrol-test/package_control-tester/tree/foo/bar",
                ("packagecontrol-test", "package_control-tester", "foo/bar")
            ),
            (
                "11",
                "https://github.com/packagecontrol-test/package_control-tester/tree/foo/bar/",
                ("packagecontrol-test", "package_control-tester", "foo/bar")
            ),
            (
                "12",
                "https://github.com/packagecontrol-test/package_control-tester/tags",
                (None, None, None)
            ),
            (
                "13",
                "https://github.com/packagecontrol-test/package_control-tester/tags/",
                (None, None, None)
            ),
            (
                "14",
                "https://github;com/packagecontrol-test/package_control-tester",
                (None, None, None)
            ),
        ),
        first_param_name_suffix=True
    )
    def repo_user_branch(self, url, result):
        client = GitHubClient(self.settings())
        self.assertEqual(result, client.user_repo_branch(url))

    def test_repo_info(self):
        client = GitHubClient(self.settings())
        self.assertEqual(
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
                "default_branch": "master"
            },
            client.repo_info("https://github.com/packagecontrol-test/package_control-tester")
        )

    def test_user_info(self):
        client = GitHubClient(self.settings())
        self.assertEqual(
            [{
                "name": "package_control-tester",
                "description": "A test of Package Control upgrade messages with "
                               "explicit versions, but date-based releases.",
                "homepage": "https://github.com/packagecontrol-test/package_control-tester",
                "author": "packagecontrol-test",
                "readme": "https://raw.githubusercontent.com/packagecontrol-test"
                          "/package_control-tester/master/readme.md",
                "issues": "https://github.com/packagecontrol-test/package_control-tester/issues",
                "donate": None,
                "default_branch": "master"
            }],
            client.user_info("https://github.com/packagecontrol-test")
        )

    @data(
        (
            (
                "branch_downloads",  # name
                None,  # extra_settings
                "https://github.com/packagecontrol-test/package_control-tester",  # url
                None,  # tag-prefix
                [
                    {
                        "date": LAST_COMMIT_TIMESTAMP,
                        "version": LAST_COMMIT_VERSION,
                        "url": "https://codeload.github.com/"
                               "packagecontrol-test/package_control-tester/zip/master"
                    }
                ]
            ),
            (
                "tags_downloads",
                None,
                "https://github.com/packagecontrol-test/package_control-tester/tags",
                None,
                [
                    {
                        "date": "2014-11-12 15:52:35",
                        "version": "1.0.1",
                        "url": "https://codeload.github.com/"
                               "packagecontrol-test/package_control-tester/zip/1.0.1"
                    },
                    {
                        "date": "2014-11-12 15:14:23",
                        "version": "1.0.1-beta",
                        "url": "https://codeload.github.com/"
                               "packagecontrol-test/package_control-tester/zip/1.0.1-beta"
                    },
                    {
                        "date": "2014-11-12 15:14:13",
                        "version": "1.0.0",
                        "url": "https://codeload.github.com/"
                               "packagecontrol-test/package_control-tester/zip/1.0.0"
                    },
                    {
                        "date": "2014-11-12 02:02:22",
                        "version": "0.9.0",
                        "url": "https://codeload.github.com/"
                               "packagecontrol-test/package_control-tester/zip/0.9.0"
                    }
                ]
            ),
            (
                "limited_tags_downloads",
                {"max_releases": 1},
                "https://github.com/packagecontrol-test/package_control-tester/tags",
                None,
                [
                    {
                        "date": "2014-11-12 15:52:35",
                        "version": "1.0.1",
                        "url": "https://codeload.github.com/"
                               "packagecontrol-test/package_control-tester/zip/1.0.1"
                    }
                ]
            ),
            (
                "tags_prefix_downloads",
                None,
                "https://github.com/packagecontrol-test/package_control-tester/tags",
                "win-",
                [
                    {
                        "date": "2014-11-28 20:54:15",
                        "version": "1.0.2",
                        "url": "https://codeload.github.com/"
                               "packagecontrol-test/package_control-tester/zip/win-1.0.2"
                    }
                ]
            ),
        ),
        first_param_name_suffix=True
    )
    def download_info(self, extra_settings, url, tag_prefix, result):
        client = GitHubClient(self.settings(extra_settings))
        self.assertEqual(result, client.download_info(url, tag_prefix))

    @data(
        (
            (
                "via_repo_url",  # name
                None,  # extra_settings
                "https://github.com/packagecontrol-test/package_control-tester",  # url
                None,  # tag-prefix
                [
                    {
                        "date": LAST_COMMIT_TIMESTAMP,
                        "version": LAST_COMMIT_VERSION,
                        "url": "https://codeload.github.com/"
                               "packagecontrol-test/package_control-tester/zip/master"
                    }
                ]
            ),
        ),
        first_param_name_suffix=True
    )
    def download_info_from_branch(self, extra_settings, url, branch, result):
        client = GitHubClient(self.settings(extra_settings))
        self.assertEqual(result, client.download_info_from_branch(url, branch))

    @data(
        (
            (
                "via_repo_url",
                None,
                "https://github.com/packagecontrol-test/package_control-tester",
                None,
                [
                    {
                        "date": "2014-11-12 15:52:35",
                        "version": "1.0.1",
                        "url": "https://codeload.github.com/"
                               "packagecontrol-test/package_control-tester/zip/1.0.1"
                    },
                    {
                        "date": "2014-11-12 15:14:23",
                        "version": "1.0.1-beta",
                        "url": "https://codeload.github.com/"
                               "packagecontrol-test/package_control-tester/zip/1.0.1-beta"
                    },
                    {
                        "date": "2014-11-12 15:14:13",
                        "version": "1.0.0",
                        "url": "https://codeload.github.com/"
                               "packagecontrol-test/package_control-tester/zip/1.0.0"
                    },
                    {
                        "date": "2014-11-12 02:02:22",
                        "version": "0.9.0",
                        "url": "https://codeload.github.com/"
                               "packagecontrol-test/package_control-tester/zip/0.9.0"
                    }
                ]
            ),
            (
                "via_repo_url_limited",
                {"max_releases": 1},
                "https://github.com/packagecontrol-test/package_control-tester",
                None,
                [
                    {
                        "date": "2014-11-12 15:52:35",
                        "version": "1.0.1",
                        "url": "https://codeload.github.com/"
                               "packagecontrol-test/package_control-tester/zip/1.0.1"
                    }
                ]
            ),
            (
                "via_repo_url_with_prefix",
                None,
                "https://github.com/packagecontrol-test/package_control-tester",
                "win-",
                [
                    {
                        "date": "2014-11-28 20:54:15",
                        "version": "1.0.2",
                        "url": "https://codeload.github.com/"
                               "packagecontrol-test/package_control-tester/zip/win-1.0.2"
                    }
                ]
            ),
        ),
        first_param_name_suffix=True
    )
    def download_info_from_tags(self, extra_settings, url, tag_prefix, result):
        client = GitHubClient(self.settings(extra_settings))
        self.assertEqual(result, client.download_info_from_tags(url, tag_prefix))

    @data(
        (
            (
                # url
                "https://github.com/packagecontrol-test/package_control-tester",
                # asset_templates
                [
                    # asset name pattern, { selectors }
                    ("package_control-tester.sublime-package", {}),
                ],
                # tag prefix
                None,
                # results (note: test repo"s don"t provide release assests to test against, unfortunatelly)
                [
                    # {
                    #     "date": "2014-11-12 15:52:35",
                    #     "version": "1.0.1",
                    #     "url": "https://github.com/packagecontrol-test/package_control-tester/"
                    #            "downloads/releases/1.0.1/package_control-tester.sublime-package"
                    # },
                    # {
                    #     "date": "2014-11-12 15:14:23",
                    #     "version": "1.0.1-beta",
                    #     "url": "https://github.com/packagecontrol-test/package_control-tester/"
                    #            "downloads/releases/1.0.1-beta/package_control-tester.sublime-package"
                    # },
                    # {
                    #     "date": "2014-11-12 15:14:13",
                    #     "version": "1.0.0",
                    #     "url": "https://github.com/packagecontrol-test/package_control-tester/"
                    #            "downloads/releases/1.0.0/package_control-tester.sublime-package"
                    # },
                    # {
                    #     "date": "2014-11-12 02:02:22",
                    #     "version": "0.9.0",
                    #     "url": "https://github.com/packagecontrol-test/package_control-tester/"
                    #            "downloads/releases/0.9.0/package_control-tester.sublime-package"
                    # }
                ]
            ),
            (
                "https://github.com/packagecontrol-test/package_control-tester",
                [
                    (
                        "package_control-tester-st4???.sublime-package",
                        {"sublime_text": ">=4107"}
                    )
                ],
                None,
                []
            ),
            (
                "https://github.com/packagecontrol-test/package_control-tester",
                [
                    (
                        "package_control-tester-st${st_build}.sublime-package",
                        {"sublime_text": ">=4107"}
                    )
                ],
                None,
                []
            ),
            (
                "https://github.com/packagecontrol-test/package_control-tester",
                [
                    (
                        "package_control-tester-${platform}.sublime-package",
                        {"platforms": ["*"]}
                    )
                ],
                None,
                []
            ),
            (
                "https://github.com/packagecontrol-test/package_control-tester",
                [
                    (
                        "package_control-tester-${platform}.sublime-package",
                        {"platforms": ["windows-x64", "linux-x64"]}
                    )
                ],
                None,
                []
            ),
            (
                "https://github.com/packagecontrol-test/package_control-tester",
                [
                    (
                        "package_control-tester-win-amd64.sublime-package",
                        {"platforms": ["windows-x64"]}
                    ),
                    (
                        "package_control-tester-win-arm64.sublime-package",
                        {"platforms": ["windows-arm64"]}
                    ),
                    (
                        "package_control-tester-linux-aarch64.sublime-package",
                        {"platforms": ["linux-arm64"]}
                    )
                ],
                None,
                []
            ),
        )
    )
    def download_info_from_releases(self, url, asset_templates, tag_prefix, result):
        client = GitHubClient(self.settings())
        self.assertEqual(result, client.download_info_from_releases(url, asset_templates, tag_prefix))
