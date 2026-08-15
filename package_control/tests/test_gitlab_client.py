import unittest

from ..clients.gitlab_client import GitLabClient
from ..http_cache import HttpCache
from ._data_decorator import data_decorator, data

from ._config import (
    DEBUG,
    GL_PASS,
    GL_USER,
    USER_AGENT,
)


@data_decorator
class GitLabClientTests(unittest.TestCase):
    maxDiff = None

    def settings(self, extra=None):
        if not GL_PASS:
            self.skipTest("GitLab personal access token for %s not set via env var GL_PASS" % GL_USER)

        settings = {
            "debug": DEBUG,
            "cache": HttpCache(604800),
            "cache_length": 604800,
            "user_agent": USER_AGENT,
            "http_basic_auth": {
                "gitlab.com": [GL_USER, GL_PASS]
            }
        }
        if extra:
            settings.update(extra)

        return settings

    @data(
        (
            (
                "1",
                "https://gitlab.com",
                (None, None, None)
            ),
            (
                "2",
                "https://gitlab.com/",
                (None, None, None)
            ),
            (
                "3",
                "https://gitlab.com/packagecontrol-test",
                ("packagecontrol-test", None, None)
            ),
            (
                "4",
                "https://gitlab.com/packagecontrol-test/",
                ("packagecontrol-test", None, None)
            ),
            (
                "5",
                "https://gitlab.com/packagecontrol-test/package_control-tester",
                ("packagecontrol-test", "package_control-tester", None)
            ),
            (
                "6",
                "https://gitlab.com/packagecontrol-test/package_control-tester/",
                ("packagecontrol-test", "package_control-tester", None)
            ),
            (
                "7",
                "https://gitlab.com/packagecontrol-test/package_control-tester.git",
                ("packagecontrol-test", "package_control-tester", None)
            ),
            (
                "8",
                "https://gitlab.com/packagecontrol-test/package_control-tester/-/tree/master",
                ("packagecontrol-test", "package_control-tester", "master")
            ),
            (
                "9",
                "https://gitlab.com/packagecontrol-test/package_control-tester/-/tree/master/",
                ("packagecontrol-test", "package_control-tester", "master")
            ),
            (
                "10",
                "https://gitlab.com/packagecontrol-test/package_control-tester/-/tree/foo/bar",
                ("packagecontrol-test", "package_control-tester", "foo/bar")
            ),
            (
                "11",
                "https://gitlab.com/packagecontrol-test/package_control-tester/-/tree/foo/bar/",
                ("packagecontrol-test", "package_control-tester", "foo/bar")
            ),
            (
                "12",
                "https://gitlab.com/packagecontrol-test/package_control-tester/-/tags",
                (None, None, None)
            ),
            (
                "13",
                "https://gitlab.com/packagecontrol-test/package_control-tester/-/tags/",
                (None, None, None)
            ),
            (
                "14",
                "https://gitlab;com/packagecontrol-test/package_control-tester",
                (None, None, None)
            ),
        ),
        first_param_name_suffix=True
    )
    def repo_user_branch(self, url, result):
        client = GitLabClient(self.settings())
        self.assertEqual(result, client.user_repo_branch(url))

    def test_repo_info_client(self):
        client = GitLabClient(self.settings({"min_api_calls": True}))
        self.assertEqual(
            {
                "name": "package_control-tester",
                "description":
                    "A test of Package Control upgrade messages with explicit versions, but date-based releases.",
                "homepage": "https://gitlab.com/packagecontrol-test/package_control-tester",
                "readme":
                    "https://gitlab.com/packagecontrol-test/package_control-tester/-/raw/master/readme.md",
                "author": "packagecontrol-test",
                "issues": None,
                "donate": None,
                "default_branch": "master"
            },
            client.repo_info(
                "https://gitlab.com/packagecontrol-test/package_control-tester"
            )
        )

    def test_repo_info_server(self):
        client = GitLabClient(self.settings({"min_api_calls": False}))
        self.assertEqual(
            {
                "name": "package_control-tester",
                "description":
                    "A test of Package Control upgrade messages with explicit versions, but date-based releases.",
                "homepage": "https://gitlab.com/packagecontrol-test/package_control-tester",
                "readme":
                    "https://gitlab.com/packagecontrol-test/package_control-tester/-/raw/master/readme.md",
                "author": "packagecontrol-test",
                "issues": None,
                "donate": None,
                "default_branch": "master"
            },
            client.repo_info(
                "https://gitlab.com/packagecontrol-test/package_control-tester"
            )
        )

    @data(
        (
            (
                "branch_downloads",  # name
                None,  # extra_settings
                "https://gitlab.com/packagecontrol-test/package_control-tester",  # url
                None,  # tag-prefix
                [
                    {
                        "date": "2020-07-15 10:50:38",
                        "version": "2020.07.15.10.50.38",
                        "url":
                            "https://gitlab.com/packagecontrol-test/package_control-tester"
                            "/-/archive/master/package_control-tester-master.zip"
                    }
                ]
            ),
            (
                "tags_downloads",
                None,
                "https://gitlab.com/packagecontrol-test/package_control-tester/-/tags",
                None,
                [
                    {
                        "date": "2020-07-15 10:50:38",
                        "version": "1.0.1",
                        "url":
                            "https://gitlab.com/packagecontrol-test/package_control-tester"
                            "/-/archive/1.0.1/package_control-tester-1.0.1.zip"
                    }
                ]
            ),
            (
                "tags_with_prefix_downloads",
                None,
                "https://gitlab.com/packagecontrol-test/package_control-tester/-/tags",
                "win-",
                [
                    {
                        "date": "2020-07-15 10:50:38",
                        "version": "1.0.1",
                        "url":
                            "https://gitlab.com/packagecontrol-test/package_control-tester"
                            "/-/archive/win-1.0.1/package_control-tester-win-1.0.1.zip"
                    }
                ]
            ),
        ),
        first_param_name_suffix=True
    )
    def download_info(self, extra_settings, url, tag_prefix, result):
        client = GitLabClient(self.settings(extra_settings))
        self.assertEqual(result, client.download_info(url, tag_prefix))

    @data(
        (
            (
                "via_repo_url",
                None,
                "https://gitlab.com/packagecontrol-test/package_control-tester",
                None,
                [
                    {
                        "date": "2020-07-15 10:50:38",
                        "version": "2020.07.15.10.50.38",
                        "url":
                            "https://gitlab.com/packagecontrol-test/package_control-tester"
                            "/-/archive/master/package_control-tester-master.zip"
                    }
                ]
            ),
        ),
        first_param_name_suffix=True
    )
    def download_info_from_branch(self, extra_settings, url, branch, result):
        client = GitLabClient(self.settings(extra_settings))
        self.assertEqual(result, client.download_info_from_branch(url, branch))

    @data(
        (
            (
                "via_repo_url",
                None,
                "https://gitlab.com/packagecontrol-test/package_control-tester",
                None,
                [
                    {
                        "date": "2020-07-15 10:50:38",
                        "version": "1.0.1",
                        "url":
                            "https://gitlab.com/packagecontrol-test/package_control-tester"
                            "/-/archive/1.0.1/package_control-tester-1.0.1.zip"
                    }
                ]
            ),
            (
                "via_repo_url_with_prefix",
                None,
                "https://gitlab.com/packagecontrol-test/package_control-tester",
                "win-",
                [
                    {
                        "date": "2020-07-15 10:50:38",
                        "version": "1.0.1",
                        "url":
                            "https://gitlab.com/packagecontrol-test/package_control-tester"
                            "/-/archive/win-1.0.1/package_control-tester-win-1.0.1.zip"
                    }
                ]
            ),
        ),
        first_param_name_suffix=True
    )
    def download_info_from_tags(self, extra_settings, url, tag_prefix, result):
        client = GitLabClient(self.settings(extra_settings))
        self.assertEqual(result, client.download_info_from_tags(url, tag_prefix))

    @data(
        (
            (
                # url
                "https://gitlab.com/packagecontrol-test/package_control-tester",
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
                    #     "date": "2020-07-15 10:50:38",
                    #     "version": "1.0.1",
                    #     "url":
                    #         "https://gitlab.com/packagecontrol-test/package_control-tester"
                    #         "/-/releases/1.0.1/downloads/package_control-tester.sublime-package"
                    # }
                ]
            ),
            (
                "https://gitlab.com/packagecontrol-test/package_control-tester",
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
                "https://gitlab.com/packagecontrol-test/package_control-tester",
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
                "https://gitlab.com/packagecontrol-test/package_control-tester",
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
                "https://gitlab.com/packagecontrol-test/package_control-tester",
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
                "https://gitlab.com/packagecontrol-test/package_control-tester",
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
        client = GitLabClient(self.settings())
        self.assertEqual(result, client.download_info_from_releases(url, asset_templates, tag_prefix))
