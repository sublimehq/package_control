# flake8: noqa: E121,E126,E501
import unittesting
from unittest import skipUnless

from ..http_cache import HttpCache
from ..package_registry import PackageRegistry
from ._config import (
    BB_PASS,
    BB_USER,
    DEBUG,
    GH_PASS,
    GH_USER,
    GL_PASS,
    GL_USER,
    LAST_COMMIT_TIMESTAMP,
    LAST_COMMIT_VERSION,
    TEST_FIXTURES_URI,
    USER_AGENT
)


class PackageRegistryTests(unittesting.TestCase):
    maxDiff = None

    def setUp(self):
        settings = {
            "debug": DEBUG,
            "channels": [],
            "repositories": [],
            "install_pre_releases": False,
            "cache": HttpCache(604800),
            "cache_length": 604800,
            "http_basic_auth": {
                "api.bitbucket.org": [BB_USER, BB_PASS],
                "api.github.com": [GH_USER, GH_PASS],
                "gitlab.com": [GL_USER, GL_PASS],
            },            
            "user_agent": USER_AGENT,
        }
        self.registry = PackageRegistry(settings)

    def test_merge_behavior(self):
        self.registry.settings["channels"] = [
            TEST_FIXTURES_URI + "fixture-01/channel-01.json",
            TEST_FIXTURES_URI + "fixture-01/channel-02.json",
        ]
        self.registry.settings["repositories"] = [
            TEST_FIXTURES_URI + "fixture-01/repository-00.json",
        ]
        self.assertEqual(
            [
                {
                    "details": None,
                    "name": "package-from-repository-00",
                    "author": "test-user",
                    "description": "This package is used",
                    "issues": None,
                    "homepage": None,
                    "readme": None,
                    "donate": None,
                    "labels": [],
                    "last_modified": "2021-01-01 00:00:00",
                    "previous_names": [],
                    "releases": [
                        {
                            "url": "https://server.com/downloads/test-package.sublime-package",
                            "date": "2021-01-01 00:00:00",
                            "version": "1.0.0",
                            "platforms": ["*"],
                            "sublime_text": "*",
                        }
                    ],
                    "source": TEST_FIXTURES_URI + "fixture-01/repository-00.json",
                },
                {
                    "details": None,
                    "name": "package-from-repository-01",
                    "author": "test-user",
                    "description": "This package is used",
                    "issues": None,
                    "homepage": None,
                    "readme": None,
                    "donate": None,
                    "labels": [],
                    "last_modified": "2021-01-01 00:00:00",
                    "previous_names": [],
                    "releases": [
                        {
                            "url": "https://server.com/downloads/test-package.sublime-package",
                            "date": "2021-01-01 00:00:00",
                            "version": "1.0.0",
                            "platforms": ["*"],
                            "sublime_text": "*",
                        }
                    ],
                    "source": TEST_FIXTURES_URI + "fixture-01/repository-01.json",
                },
                {
                    "details": None,
                    "name": "package-from-repository-03",
                    "author": "test-user",
                    "description": "This package is used",
                    "issues": None,
                    "homepage": None,
                    "readme": None,
                    "donate": None,
                    "labels": [],
                    "last_modified": "2023-01-01 00:00:00",
                    "previous_names": [],
                    "releases": [
                        {
                            "url": "https://server.com/downloads/test-package.sublime-package",
                            "date": "2023-01-01 00:00:00",
                            "version": "3.0.0",
                            "platforms": ["*"],
                            "sublime_text": "*",
                        }
                    ],
                    "source": TEST_FIXTURES_URI + "fixture-01/repository-03.json",
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
                    "source": TEST_FIXTURES_URI + "fixture-01/repository-04.json",
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
                    "source": TEST_FIXTURES_URI + "fixture-01/repository-05.json",
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
                    "source": TEST_FIXTURES_URI + "fixture-01/repository-06.json",
                },
            ],
            self.registry.get_packages(),
        )

    def test_get_library_names_mapped(self):
        """
        Verify translation from legacy dependency names to PEP491 distribution names,
        which they are accessed by, regardless their official PyPi "name" field.
        """
        self.registry.settings.update({
            "repositories": [TEST_FIXTURES_URI + "fixture-01/repository-00.json"],
        })
        self.assertEqual({"beautifulsoup4", "enum34", "jinja2"}, self.registry.get_libray_names())

    def test_get_libraries_mapped(self):
        self.registry.settings.update({
            "repositories": [TEST_FIXTURES_URI + "fixture-01/repository-00.json"],
        })
        self.assertEqual(
            [
                {
                    # test name translation from "bs4" to "beautifulsoup4"
                    "name": "beautifulsoup4",
                    "description": "Beautiful Soup is a Python library for pulling data out of HTML and XML files - https://www.crummy.com/software/BeautifulSoup/",
                    "author": "jlegewie",
                    "issues": "https://github.com/jlegewie/sublime-beautifulsoup4/issues",
                    "releases": [
                        {
                            "url": "https://codeload.github.com/jlegewie/sublime-beautifulsoup4/zip/bs4.zip",
                            "date": "2014-01-01 10:00:00",
                            "version": "1.0.0",
                            "platforms": ["*"],
                            "python_versions": ["3.3", "3.8", "3.14"],
                            "sublime_text": ">=3000",
                        }
                    ],
                    "source": TEST_FIXTURES_URI + "fixture-01/repository-00.json"
                },
                {
                    # test name translation from "enum" to "enum34"
                    "name": "enum34",
                    "description": "Python enum module",
                    "author": "FichteFoll",
                    "issues": "https://github.com/packagecontrol/enum/issues",
                    "releases": [
                        {
                            "url": "https://codeload.github.com/packagecontrol/enum/zip/enum.zip",
                            "date": "2014-01-01 10:00:00",
                            "version": "1.0.0",
                            "platforms": ["*"],
                            "python_versions": ["3.3", "3.8", "3.14"],
                            "sublime_text": "*"
                        }
                    ],
                    "source": TEST_FIXTURES_URI + "fixture-01/repository-00.json"
                },
                {
                    # test name translation from "python-jinja2" to "Jinja2"
                    "name": "Jinja2",
                    "description": "Python Jinja2 module",
                    "author": "FichteFoll",
                    "issues": "https://github.com/packagecontrol/jinja2/issues",
                    "releases": [
                        {
                            "url": "https://codeload.github.com/packagecontrol/jinja2/zip/python-jinja2.zip",
                            "date": "2014-01-01 10:00:00",
                            "version": "1.0.0",
                            "platforms": ["*"],
                            "python_versions": ["3.3", "3.8", "3.14"],
                            "sublime_text": "*",
                        }
                    ],
                    "source": TEST_FIXTURES_URI + "fixture-01/repository-00.json"
                }
            ],
            self.registry.get_libraries()
        )

    @skipUnless(BB_PASS, "Needs authentication.")
    def test_get_packages_from_bitbucket(self):
        self.registry.settings.update({
            "repositories": ["https://bitbucket.org/wbond/package_control-tester"],
        })
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
            self.registry.get_packages()
        )

    @skipUnless(BB_PASS, "Needs authentication.")
    def test_get_packages_from_bitbucket_mapped(self):
        self.registry.settings.update({
            "repositories": ["https://bitbucket.org/wbond/package_control-tester"],
            "package_name_map": {"package_control-tester": "Package Control Tester"},
        })
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
            self.registry.get_packages()
        )

    @skipUnless(GH_PASS, "Needs authentication.")
    def test_get_packages_from_github(self):
        self.registry.settings.update({
            "repositories": ["https://github.com/packagecontrol-test/package_control-tester"],
        })
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
                    "source": "https://github.com/packagecontrol-test/package_control-tester",
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
            self.registry.get_packages()
        )

    @skipUnless(GH_PASS, "Needs authentication.")
    def test_get_packages_from_github_mapped(self):
        self.registry.settings.update({
            "repositories": ["https://github.com/packagecontrol-test/package_control-tester"],
            "package_name_map": {"package_control-tester": "Package Control Tester"},
        })
        self.assertEqual(
            [
               {
                    "name": "Package Control Tester",
                    "description": "A test of Package Control upgrade messages with "
                                   "explicit versions, but date-based releases.",
                    "homepage": "https://github.com/packagecontrol-test/package_control-tester",
                    "author": "packagecontrol-test",
                    "readme": "https://raw.githubusercontent.com/packagecontrol-test"
                              "/package_control-tester/master/readme.md",
                    "issues": "https://github.com/packagecontrol-test/package_control-tester/issues",
                    "donate": None,
                    "source": "https://github.com/packagecontrol-test/package_control-tester",
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
            self.registry.get_packages()
        )

    @skipUnless(GL_PASS, "Needs authentication.")
    def test_get_packages_from_gitlab(self):
        self.registry.settings.update({
            "repositories": ["https://gitlab.com/packagecontrol-test/package_control-tester"],
        })
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
                    "source": "https://gitlab.com/packagecontrol-test/package_control-tester",
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
            self.registry.get_packages()
        )

    @skipUnless(GL_PASS, "Needs authentication.")
    def test_get_packages_from_gitlab_mapped(self):
        self.registry.settings.update({
            "repositories": ["https://gitlab.com/packagecontrol-test/package_control-tester"],
            "package_name_map": {"package_control-tester": "Package Control Tester"},
        })
        self.assertEqual(
            [
                {
                    "name": "Package Control Tester",
                    "description": "A test of Package Control upgrade messages with "
                                   "explicit versions, but date-based releases.",
                    "homepage": "https://gitlab.com/packagecontrol-test/package_control-tester",
                    "author": "packagecontrol-test",
                    "readme": "https://gitlab.com/packagecontrol-test/"
                              "package_control-tester/-/raw/master/readme.md",
                    "issues": None,
                    "donate": None,
                    "source": "https://gitlab.com/packagecontrol-test/package_control-tester",
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
            self.registry.get_packages()
        )
