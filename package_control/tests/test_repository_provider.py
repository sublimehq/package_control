# flake8: noqa: E121,E126,E501
import unittest

from ..http_cache import HttpCache
from ..providers.repository_provider import RepositoryProvider
from ._data_decorator import data_decorator, data

from ._config import (
    DEBUG,
    TEST_FIXTURES_URI,
    TEST_REPOSITORY_URI
)

TEST_FIXTURE_01_URL = TEST_FIXTURES_URI + "fixture-01/"


@data_decorator
class RepositoryProviderTests(unittest.TestCase):
    maxDiff = None

    def settings(self):
        return {
            "debug": DEBUG,
        }

    def test_merge_behavior(self):
        provider = RepositoryProvider(TEST_FIXTURE_01_URL + "repository-04.json", self.settings())
        self.assertEqual(
            [
                {
                    # contained in repository-04, but ignored in registry as also in repository-01,
                    # included by channel-01
                    "details": None,
                    "name": "package-from-repository-01",
                    "author": "test-user",
                    "description": "This is a package",
                    "issues": None,
                    "homepage": None,
                    "readme": None,
                    "donate": None,
                    "labels": [],
                    "last_modified": "2024-01-01 00:00:00",
                    "previous_names": [],
                    "releases": [
                        {
                            "url": "https://server.com/downloads/test-package.sublime-package",
                            "date": "2024-01-01 00:00:00",
                            "version": "4.0.0",
                            "platforms": ["*"],
                            "sublime_text": "*",
                        }
                    ],
                    "source": TEST_FIXTURE_01_URL + "repository-04.json",
                },
                {
                    # contained in repository-06, included by repository-04,
                    # but ignored in registry as also in repository-03
                    "details": None,
                    "name": "package-from-repository-03",
                    "author": "test-user",
                    "description": "This is a package",
                    "issues": None,
                    "homepage": None,
                    "readme": None,
                    "donate": None,
                    "labels": [],
                    "last_modified": "2026-01-01 00:00:00",
                    "previous_names": [],
                    "releases": [
                        {
                            "url": "https://server.com/downloads/test-package.sublime-package",
                            "date": "2026-01-01 00:00:00",
                            "version": "6.0.0",
                            "platforms": ["*"],
                            "sublime_text": "*",
                        }
                    ],
                    "source": TEST_FIXTURE_01_URL + "repository-06.json",
                },
                {
                    "details": None,
                    "name": "package-from-repository-04",
                    "author": "test-user",
                    "description": "This package is used",
                    "issues": None,
                    "homepage": None,
                    "readme": None,
                    "donate": None,
                    "labels": [],
                    "last_modified": "2024-01-01 00:00:00",
                    "previous_names": [],
                    "releases": [
                        {
                            "url": "https://server.com/downloads/test-package.sublime-package",
                            "date": "2024-01-01 00:00:00",
                            "version": "4.0.0",
                            "platforms": ["*"],
                            "sublime_text": "*",
                        }
                    ],
                    "source": TEST_FIXTURE_01_URL + "repository-04.json",
                },
                {
                    "details": None,
                    "name": "package-from-repository-05",
                    "author": "test-user",
                    "description": "This package is used",
                    "issues": None,
                    "homepage": None,
                    "readme": None,
                    "donate": None,
                    "labels": [],
                    "last_modified": "2025-01-01 00:00:00",
                    "previous_names": [],
                    "releases": [
                        {
                            "url": "https://server.com/downloads/test-package.sublime-package",
                            "date": "2025-01-01 00:00:00",
                            "version": "5.0.0",
                            "platforms": ["*"],
                            "sublime_text": "*",
                        }
                    ],
                    "source": TEST_FIXTURE_01_URL + "repository-05.json",
                },
                {
                    "details": None,
                    "name": "package-from-repository-06",
                    "author": "test-user",
                    "description": "This package is used",
                    "issues": None,
                    "homepage": None,
                    "readme": None,
                    "donate": None,
                    "labels": [],
                    "last_modified": "2026-01-01 00:00:00",
                    "previous_names": [],
                    "releases": [
                        {
                            "url": "https://server.com/downloads/test-package.sublime-package",
                            "date": "2026-01-01 00:00:00",
                            "version": "6.0.0",
                            "platforms": ["*"],
                            "sublime_text": "*",
                        }
                    ],
                    "source": TEST_FIXTURE_01_URL + "repository-06.json",
                },
            ],
            provider.get_packages()
        )

    @data(
        (
            (
                # test_case name
                "10",
                # repository url
                TEST_REPOSITORY_URI + "repository-1.0.json",
                # expected result
                []  # libraries not supported
            ),
            (
                "12",
                TEST_REPOSITORY_URI + "repository-1.2.json",
                []  # libraries not supported
            ),
            (
                "20",
                TEST_REPOSITORY_URI + "repository-2.0-explicit.json",
                []  # libraries not supported
            ),
            (
                "300",
                TEST_REPOSITORY_URI + "repository-3.0.0-explicit.json",
                [
                    {
                        "name": "bz2",
                        "author": "wbond",
                        "description": "Python bz2 module",
                        "issues": "https://github.com/wbond/package_control/issues",
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-explicit.json",
                        "releases": [
                            {
                                "date": "2014-11-12 02:02:22",
                                "version": "1.0.0",
                                "url": "https://packagecontrol.io/bz2.sublime-package",
                                "sublime_text": "*",
                                "platforms": ["*"],
                                "python_versions": ["3.3"]
                            }
                        ]
                    },
                    {
                        "name": "ssl-linux",
                        "description": "Python _ssl module for Linux",
                        "author": "wbond",
                        "issues": "https://github.com/wbond/package_control/issues",
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-explicit.json",
                        "releases": [
                            {
                                "date": "1970-01-01 00:00:00",
                                "version": "1.0.0",
                                "url": "http://packagecontrol.io/ssl-linux.sublime-package",
                                "sublime_text": "*",
                                "platforms": ["linux"],
                                "python_versions": ["3.3"],
                                "sha256": "d12a2ca2843b3c06a834652e9827a29f88872bb31bd64230775f3dbe12e0ebd4"
                            }
                        ]
                    },
                    {
                        "name": "ssl-windows",
                        "description": "Python _ssl module for Sublime Text 2 on Windows",
                        "author": "wbond",
                        "issues": "https://github.com/wbond/package_control/issues",
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-explicit.json",
                        "releases": [
                            {
                                "date": "1970-01-01 00:00:00",
                                "version": "1.0.0",
                                "url": "http://packagecontrol.io/ssl-windows.sublime-package",
                                "sublime_text": "<3000",
                                "platforms": ["windows"],
                                "python_versions": ["3.3"],
                                "sha256": "efe25e3bdf2e8f791d86327978aabe093c9597a6ceb8c2fb5438c1d810e02bea"
                            }
                        ]
                    }
                ]
            ),
            (
                "400",
                TEST_REPOSITORY_URI + "repository-4.0.0-explicit.json",
                [
                    {
                        "name": "bz2",
                        "author": "wbond",
                        "description": "Python bz2 module",
                        "issues": "https://github.com/wbond/package_control/issues",
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-explicit.json",
                        "releases": [
                            {
                                "date": "2014-11-12 02:02:22",
                                "version": "1.0.0",
                                "url": "https://packagecontrol.io/bz2.sublime-package",
                                "sublime_text": "*",
                                "platforms": ["*"],
                                "python_versions": ["3.3"]
                            }
                        ]
                    },
                    {
                        "name": "ssl-linux",
                        "description": "Python _ssl module for Linux",
                        "author": "wbond",
                        "issues": "https://github.com/wbond/package_control/issues",
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-explicit.json",
                        "releases": [
                            {
                                "date": "1970-01-01 00:00:00",
                                "version": "1.0.0",
                                "url": "http://packagecontrol.io/ssl-linux.sublime-package",
                                "sublime_text": "*",
                                "platforms": ["linux"],
                                "python_versions": ["3.3", "3.8"],
                                "sha256": "d12a2ca2843b3c06a834652e9827a29f88872bb31bd64230775f3dbe12e0ebd4"
                            }
                        ]
                    },
                    {
                        "name": "ssl-windows",
                        "description": "Python _ssl module for Sublime Text 2 on Windows",
                        "author": "wbond",
                        "issues": "https://github.com/wbond/package_control/issues",
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-explicit.json",
                        "releases": [
                            {
                                "date": "1970-01-01 00:00:00",
                                "version": "1.0.0",
                                "url": "http://packagecontrol.io/ssl-windows.sublime-package",
                                "sublime_text": "<3000",
                                "platforms": ["windows"],
                                "python_versions": ["3.3"],
                                "sha256": "efe25e3bdf2e8f791d86327978aabe093c9597a6ceb8c2fb5438c1d810e02bea"
                            }
                        ]
                    }
                ]
            ),
        ),
        first_param_name_suffix=True
    )
    def get_libraries(self, url, result):
        provider = RepositoryProvider(url, self.settings())
        self.assertEqual(result, provider.get_libraries())

    @data(
        (
            (
                # test_case name
                "10",
                # repository url
                TEST_REPOSITORY_URI + "repository-1.0.json",
                # expected result
                []  # no longer supported by PC4.0+, empty results
            ),
            (
                "12",
                TEST_REPOSITORY_URI + "repository-1.2.json",
                []  # no longer supported by PC4.0+, empty results
            ),
            (
                "20_explicit",
                TEST_REPOSITORY_URI + "repository-2.0-explicit.json",
                [
                   {
                        "details": None,
                        "name": "package_control-tester-2.0",
                        "author": "packagecontrol",
                        "description": "A test of Package Control upgrade messages with "
                                       "explicit versions, but date-based releases.",
                        "issues": None,
                        "homepage": "https://github.com/packagecontrol-test/package_control-tester",
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "source": TEST_REPOSITORY_URI + "repository-2.0-explicit.json",
                        "last_modified": "2014-11-12 15:52:35",
                        "releases": [
                            {
                                "version": "1.0.1",
                                "date": "2014-11-12 15:52:35",
                                "url": "https://codeload.github.com/packagecontrol-test"
                                       "/package_control-tester/zip/1.0.1",
                                "sublime_text": "*",
                                "platforms": ["windows"]
                            },
                            {
                                "version": "1.0.1-beta",
                                "date": "2014-11-12 15:14:23",
                                "url": "https://codeload.github.com/packagecontrol-test"
                                       "/package_control-tester/zip/1.0.1-beta",
                                "sublime_text": "*",
                                "platforms": ["windows"]
                            },
                            {
                                "version": "1.0.0",
                                "date": "2014-11-12 15:14:13",
                                "url": "https://codeload.github.com/packagecontrol-test"
                                       "/package_control-tester/zip/1.0.0",
                                "sublime_text": "*",
                                "platforms": ["*"]
                            },
                            {
                                "version": "0.9.0",
                                "date": "2014-11-12 02:02:22",
                                "url": "https://codeload.github.com/packagecontrol-test"
                                       "/package_control-tester/zip/0.9.0",
                                "sublime_text": "<3000",
                                "platforms": ["*"]
                            }
                        ]
                    }
                ]
            ),
            (
                "20_github_details",
                TEST_REPOSITORY_URI + "repository-2.0-github_details.json",
                [
                    {
                        "details": "https://github.com/packagecontrol-test/package_control-tester",
                        "name": "package_control-tester-2.0-gh",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "platforms": ["*"],
                                "sublime_text": "<3000",
                                "tags": True
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-2.0-github_details.json",
                    }
                ]
            ),
            (
                "20_bitbucket_details",
                TEST_REPOSITORY_URI + "repository-2.0-bitbucket_details.json",
                [
                    {
                        "details": "https://bitbucket.org/wbond/package_control-tester",
                        "name": "package_control-tester-2.0-bb",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "platforms": ["*"],
                                "sublime_text": "<3000",
                                "tags": True
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-2.0-bitbucket_details.json",
                    }
                ]
            ),
            (
                "300_explicit",
                TEST_REPOSITORY_URI + "repository-3.0.0-explicit.json",
                [
                   {
                        "details": None,
                        "name": "package_control-tester-3.0.0",
                        "author": ["packagecontrol", "wbond"],
                        "description": "A test of Package Control upgrade messages with "
                                       "explicit versions, but date-based releases.",
                        "homepage": "https://github.com/packagecontrol-test/package_control-tester",
                        "issues": None,
                        "readme": None,
                        "donate": "https://gratipay.com/wbond/",
                        "previous_names": [],
                        "labels": [],
                        "last_modified": "2014-11-12 15:52:35",
                        "releases": [
                            {
                                "version": "1.0.1",
                                "date": "2014-11-12 15:52:35",
                                "url": "https://codeload.github.com/packagecontrol-test"
                                       "/package_control-tester/zip/1.0.1",
                                "sublime_text": "*",
                                "platforms": ["windows"],
                                "libraries": ["bz2"],
                            },
                            {
                                "version": "1.0.1-beta",
                                "date": "2014-11-12 15:14:23",
                                "url": "https://codeload.github.com/packagecontrol-test"
                                       "/package_control-tester/zip/1.0.1-beta",
                                "sublime_text": "*",
                                "platforms": ["windows"]
                            },
                            {
                                "version": "1.0.0",
                                "date": "2014-11-12 15:14:13",
                                "url": "https://codeload.github.com/packagecontrol-test"
                                       "/package_control-tester/zip/1.0.0",
                                "sublime_text": "*",
                                "platforms": ["*"]
                            },
                            {
                                "version": "0.9.0",
                                "date": "2014-11-12 02:02:22",
                                "url": "https://codeload.github.com/packagecontrol-test"
                                       "/package_control-tester/zip/0.9.0",
                                "sublime_text": "<3000",
                                "platforms": ["*"]
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-explicit.json",
                    }
                ]
            ),
            (
                "300_github",
                TEST_REPOSITORY_URI + "repository-3.0.0-github_releases.json",
                [
                    {
                        "details": "https://github.com/packagecontrol-test/package_control-tester",
                        "name": "package_control-tester-3.0.0-gh-branch",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "branch": "master",
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-github_releases.json",
                    },
                    {
                        "details": "https://github.com/packagecontrol-test/package_control-tester",
                        "name": "package_control-tester-3.0.0-gh-tags",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "tags": True,
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-github_releases.json",
                    },
                    {
                        "details": None,
                        "name": "package_control-tester-3.0.0-gh-tags_base",
                        "author": "packagecontrol",
                        "description": "A test of Package Control upgrade messages with explicit versions, but date-based releases.",
                        "homepage": "https://github.com/packagecontrol-test/package_control-tester",
                        "issues": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "base": "https://github.com/packagecontrol-test/package_control-tester",
                                "tags": True,
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-github_releases.json",
                    },
                    {
                        "details": "https://github.com/packagecontrol-test/package_control-tester",
                        "name": "package_control-tester-3.0.0-gh-tags_prefix",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "tags": "win-",
                                "platforms": ["windows"],
                                "sublime_text": "<3000",
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-github_releases.json",
                    },
                ]
            ),
            (
                "300_gitlab",
                TEST_REPOSITORY_URI + "repository-3.0.0-gitlab_releases.json",
                [
                    {
                        "details": "https://gitlab.com/packagecontrol-test/package_control-tester",
                        "name": "package_control-tester-3.0.0-gl-branch",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "branch": "master",
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-gitlab_releases.json",
                    },
                    {
                        "details": "https://gitlab.com/packagecontrol-test/package_control-tester",
                        "name": "package_control-tester-3.0.0-gl-tags",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "tags": True,
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-gitlab_releases.json",
                    },
                    {
                        "details": None,
                        "name": "package_control-tester-3.0.0-gl-tags_base",
                        "author": "packagecontrol",
                        "description": "A test of Package Control upgrade messages with explicit versions, but date-based releases.",
                        "homepage": "https://gitlab.com/packagecontrol-test/package_control-tester",
                        "issues": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "base": "https://gitlab.com/packagecontrol-test/package_control-tester",
                                "tags": True,
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-gitlab_releases.json",
                    },
                    {
                        "details": "https://gitlab.com/packagecontrol-test/package_control-tester",
                        "name": "package_control-tester-3.0.0-gl-tags_prefix",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "tags": "win-",
                                "platforms": ["windows"],
                                "sublime_text": "<3000",
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-gitlab_releases.json",
                    },
                ]
            ),
            (
                "300_bitbucket",
                TEST_REPOSITORY_URI + "repository-3.0.0-bitbucket_releases.json",
                [
                    {
                        "details": "https://bitbucket.org/wbond/package_control-tester",
                        "name": "package_control-tester-3.0.0-bb-branch",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "branch": "master",
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-bitbucket_releases.json",
                    },
                    {
                        "details": "https://bitbucket.org/wbond/package_control-tester",
                        "name": "package_control-tester-3.0.0-bb-tags",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "tags": True,
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-bitbucket_releases.json",
                    },
                    {
                        "details": "https://bitbucket.org/wbond/package_control-tester",
                        "name": "package_control-tester-3.0.0-bb-tags_prefix",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "tags": "win-",
                                "platforms": ["windows"],
                                "sublime_text": "<3000",
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-3.0.0-bitbucket_releases.json",
                    },
                ]
            ),
            (
                "400_explicit",
                TEST_REPOSITORY_URI + "repository-4.0.0-explicit.json",
                [
                   {
                        "details": None,
                        "name": "package_control-tester-4.0.0",
                        "author": ["packagecontrol", "wbond"],
                        "description": "A test of Package Control upgrade messages with "
                                       "explicit versions, but date-based releases.",
                        "homepage": "https://github.com/packagecontrol-test/package_control-tester",
                        "issues": None,
                        "readme": None,
                        "donate": "https://gratipay.com/wbond/",
                        "previous_names": [],
                        "labels": [],
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-explicit.json",
                        "last_modified": "2014-11-12 15:52:35",
                        "releases": [
                            {
                                "version": "1.0.1",
                                "date": "2014-11-12 15:52:35",
                                "url": "https://codeload.github.com/packagecontrol-test"
                                       "/package_control-tester/zip/1.0.1",
                                "sublime_text": "*",
                                "platforms": ["windows"],
                                "libraries": ["bz2"],
                            },
                            {
                                "version": "1.0.1-beta",
                                "date": "2014-11-12 15:14:23",
                                "url": "https://codeload.github.com/packagecontrol-test"
                                       "/package_control-tester/zip/1.0.1-beta",
                                "sublime_text": "*",
                                "platforms": ["windows"]
                            },
                            {
                                "version": "1.0.0",
                                "date": "2014-11-12 15:14:13",
                                "url": "https://codeload.github.com/packagecontrol-test"
                                       "/package_control-tester/zip/1.0.0",
                                "sublime_text": "*",
                                "platforms": ["*"]
                            },
                            {
                                "version": "0.9.0",
                                "date": "2014-11-12 02:02:22",
                                "url": "https://codeload.github.com/packagecontrol-test"
                                       "/package_control-tester/zip/0.9.0",
                                "sublime_text": "<3000",
                                "platforms": ["*"]
                            }
                        ]
                    }
                ]
            ),
            (
                "400_github",
                TEST_REPOSITORY_URI + "repository-4.0.0-github_releases.json",
                [
                    {
                        "details": "https://github.com/packagecontrol-test/package_control-tester",
                        "name": "package_control-tester-4.0.0-gh-branch",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "branch": "master",
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-github_releases.json",
                    },
                    {
                        "details": "https://github.com/packagecontrol-test/package_control-tester",
                        "name": "package_control-tester-4.0.0-gh-tags",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "tags": True,
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-github_releases.json",
                    },
                    {
                        "details": None,
                        "name": "package_control-tester-4.0.0-gh-tags_base",
                        "author": "packagecontrol",
                        "description": "A test of Package Control upgrade messages with explicit versions, but date-based releases.",
                        "homepage": "https://github.com/packagecontrol-test/package_control-tester",
                        "issues": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "base": "https://github.com/packagecontrol-test/package_control-tester",
                                "tags": True,
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-github_releases.json",
                    },
                    {
                        "details": "https://github.com/packagecontrol-test/package_control-tester",
                        "name": "package_control-tester-4.0.0-gh-tags_prefix",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "tags": "win-",
                                "platforms": ["windows"],
                                "sublime_text": "<3000",
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-github_releases.json",
                    },
                ]
            ),
            (
                "400_gitlab",
                TEST_REPOSITORY_URI + "repository-4.0.0-gitlab_releases.json",
                [
                    {
                        "details": "https://gitlab.com/packagecontrol-test/package_control-tester",
                        "name": "package_control-tester-4.0.0-gl-branch",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "branch": "master",
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-gitlab_releases.json",
                    },
                    {
                        "details": "https://gitlab.com/packagecontrol-test/package_control-tester",
                        "name": "package_control-tester-4.0.0-gl-tags",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "tags": True,
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-gitlab_releases.json",
                    },
                    {
                        "details": None,
                        "name": "package_control-tester-4.0.0-gl-tags_base",
                        "author": "packagecontrol",
                        "description": "A test of Package Control upgrade messages with explicit versions, but date-based releases.",
                        "homepage": "https://gitlab.com/packagecontrol-test/package_control-tester",
                        "issues": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "base": "https://gitlab.com/packagecontrol-test/package_control-tester",
                                "tags": True,
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-gitlab_releases.json",
                    },
                    {
                        "details": "https://gitlab.com/packagecontrol-test/package_control-tester",
                        "name": "package_control-tester-4.0.0-gl-tags_prefix",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "tags": "win-",
                                "platforms": ["windows"],
                                "sublime_text": "<3000",
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-gitlab_releases.json",
                    },
                ]
            ),
            (
                "400_bitbucket",
                TEST_REPOSITORY_URI + "repository-4.0.0-bitbucket_releases.json",
                [
                    {
                        "details": "https://bitbucket.org/wbond/package_control-tester",
                        "name": "package_control-tester-4.0.0-bb-branch",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "branch": "master",
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-bitbucket_releases.json",
                    },
                    {
                        "details": "https://bitbucket.org/wbond/package_control-tester",
                        "name": "package_control-tester-4.0.0-bb-tags",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "tags": True,
                                "platforms": ["*"],
                                "sublime_text": "*"
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-bitbucket_releases.json",
                    },
                    {
                        "details": "https://bitbucket.org/wbond/package_control-tester",
                        "name": "package_control-tester-4.0.0-bb-tags_prefix",
                        "author": None,
                        "description": None,
                        "issues": None,
                        "homepage": None,
                        "readme": None,
                        "donate": None,
                        "previous_names": [],
                        "labels": [],
                        "last_modified": None,
                        "releases": [
                            {
                                "tags": "win-",
                                "platforms": ["windows"],
                                "sublime_text": "<3000",
                            }
                        ],
                        "source": TEST_REPOSITORY_URI + "repository-4.0.0-bitbucket_releases.json",
                    },
                ]
            ),
        ),
        first_param_name_suffix=True
    )
    def get_packages(self, url, result):
        provider = RepositoryProvider(url, self.settings())
        self.assertEqual(result, provider.get_packages())
