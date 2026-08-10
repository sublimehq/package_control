import unittest

from ..clients.pypi_client import PyPiClient
from ..http_cache import HttpCache
from ._data_decorator import data_decorator, data

from ._config import (
    DEBUG,
    USER_AGENT,
)


@data_decorator
class PyPiClientTests(unittest.TestCase):
    maxDiff = None

    def settings(self, extra=None):
        settings = {
            "debug": DEBUG,
            "cache": HttpCache(604800),
            "cache_length": 604800,
            "user_agent": USER_AGENT
        }
        if extra:
            settings.update(extra)

        return settings

    @data(
        (
            (
                "01",
                "https://pypi.org",
                (None, None)
            ),
            (
                "02",
                "https://pypi.org/",
                (None, None)
            ),
            (
                "03",
                "https://pypi.org/project",
                (None, None)
            ),
            (
                "latest",
                "https://pypi.org/project/coverage",
                ("coverage", None)
            ),
            (
                "pinned",
                "https://pypi.org/project/coverage/4.0",
                ("coverage", "4.0")
            ),
            (
                "invalid_domain",
                "https://pypi;org/project/coverage",
                (None, None)
            ),
        ),
        first_param_name_suffix=True
    )
    def name_and_version(self, url, result):
        client = PyPiClient(self.settings())
        self.assertEqual(result, client.name_and_version(url))

    @data((("https://pypi.org/project/coverage", None),))
    def download_info(self, url, result):
        client = PyPiClient(self.settings())
        self.assertEqual(result, client.download_info(url))

    @data((("https://pypi.org/project/coverage", None),))
    def download_info_from_branch(self, url, result):
        client = PyPiClient(self.settings())
        self.assertEqual(result, client.download_info_from_branch(url))

    @data((("https://pypi.org/project/coverage", None),))
    def download_info_from_tags(self, url, result):
        client = PyPiClient(self.settings())
        self.assertEqual(result, client.download_info_from_tags(url))

    @data(
        (
            (
                # name
                "py33_pinned_01",
                # settings
                None,
                # url
                "https://pypi.org/project/coverage/4.0",
                # asset_templates
                [
                    # asset name pattern, { selectors }
                    (
                        "coverage-*-cp33-*-macosx_*_x86_64*.whl",
                        {
                            "platforms": ["osx-x64"],
                            "python_versions": ["3.3"]
                        }
                    ),
                    (
                        "coverage-*-cp33-*-win_amd64*.whl",
                        {
                            "platforms": ["windows-x64"],
                            "python_versions": ["3.3"]
                        }
                    )
                ],
                # results (note: test repo"s don"t provide release assests to test against, unfortunatelly)
                [
                    {
                        "date": "2015-09-20 15:40:43",
                        "version": "4.0",
                        "url": "https://files.pythonhosted.org/packages/98/4c"
                               "/21b72fb43ad3023f58290195f6c2504982bc20ce68036fc6136d2888b3fd"
                               "/coverage-4.0-cp33-cp33m-macosx_10_10_x86_64.whl",
                        "sha256": "b442440565e6a89dcf36a005fe50cdf235bc3c0dd23982d3bdb5fe4cd491d112",
                        "platforms": ["osx-x64"],
                        "python_versions": ["3.3"]
                    },
                    {
                        "date": "2015-09-20 15:40:53",
                        "version": "4.0",
                        "url": "https://files.pythonhosted.org/packages/09/30"
                               "/7af800f04ec49b1aaa81d9f5aa69f2d81ee988ead17fb8d98121ba32b8d2"
                               "/coverage-4.0-cp33-none-win_amd64.whl",
                        "sha256": "fb4cbddbd0fcdc87df84f612c65f0240bfa60e595dea1666401817c10064ae31",
                        "platforms": ["windows-x64"],
                        "python_versions": ["3.3"]
                    }
                ]
            ),
            (
                "py33_pinned_02",
                None,
                "https://pypi.org/project/coverage/4.0",
                [
                    (
                        "coverage-?.?-cp33-*-macosx_??_??_x86_64.whl",
                        {
                            "platforms": ["osx-x64"],
                            "python_versions": ["3.3"]
                        }
                    ),
                    (
                        "coverage-?.?-cp33-*-win_amd64.whl",
                        {
                            "platforms": ["windows-x64"],
                            "python_versions": ["3.3"]
                        }
                    )
                ],
                [
                    {
                        "date": "2015-09-20 15:40:43",
                        "version": "4.0",
                        "url": "https://files.pythonhosted.org/packages/98/4c"
                               "/21b72fb43ad3023f58290195f6c2504982bc20ce68036fc6136d2888b3fd"
                               "/coverage-4.0-cp33-cp33m-macosx_10_10_x86_64.whl",
                        "sha256": "b442440565e6a89dcf36a005fe50cdf235bc3c0dd23982d3bdb5fe4cd491d112",
                        "platforms": ["osx-x64"],
                        "python_versions": ["3.3"]
                    },
                    {
                        "date": "2015-09-20 15:40:53",
                        "version": "4.0",
                        "url": "https://files.pythonhosted.org/packages/09/30"
                               "/7af800f04ec49b1aaa81d9f5aa69f2d81ee988ead17fb8d98121ba32b8d2"
                               "/coverage-4.0-cp33-none-win_amd64.whl",
                        "sha256": "fb4cbddbd0fcdc87df84f612c65f0240bfa60e595dea1666401817c10064ae31",
                        "platforms": ["windows-x64"],
                        "python_versions": ["3.3"]
                    }
                ]
            ),
            (
                "py33_pinned_03",
                None,
                "https://pypi.org/project/coverage/4.0",
                [
                    (
                        "coverage-${version}-cp${py_version}-*-macosx_*_x86_64.whl",
                        {
                            "platforms": ["osx-x64"],
                            "python_versions": ["3.3"]
                        }
                    ),
                    (
                        "coverage-${version}-cp${py_version}-*-win_amd64.whl",
                        {
                            "platforms": ["windows-x64"],
                            "python_versions": ["3.3"]
                        }
                    )
                ],
                [
                    {
                        "date": "2015-09-20 15:40:43",
                        "version": "4.0",
                        "url": "https://files.pythonhosted.org/packages/98/4c"
                               "/21b72fb43ad3023f58290195f6c2504982bc20ce68036fc6136d2888b3fd"
                               "/coverage-4.0-cp33-cp33m-macosx_10_10_x86_64.whl",
                        "sha256": "b442440565e6a89dcf36a005fe50cdf235bc3c0dd23982d3bdb5fe4cd491d112",
                        "platforms": ["osx-x64"],
                        "python_versions": ["3.3"]
                    },
                    {
                        "date": "2015-09-20 15:40:53",
                        "version": "4.0",
                        "url": "https://files.pythonhosted.org/packages/09/30"
                               "/7af800f04ec49b1aaa81d9f5aa69f2d81ee988ead17fb8d98121ba32b8d2"
                               "/coverage-4.0-cp33-none-win_amd64.whl",
                        "platforms": ["windows-x64"],
                        "sha256": "fb4cbddbd0fcdc87df84f612c65f0240bfa60e595dea1666401817c10064ae31",
                        "python_versions": ["3.3"]
                    }
                ]
            ),
            (
                "py33_latest",
                {"max_releases": 1},
                "https://pypi.org/project/coverage",
                [
                    (
                        "coverage-${version}-cp${py_version}-*-macosx_*_x86_64.whl",
                        {
                            "platforms": ["osx-x64"],
                            "python_versions": ["3.3"]
                        }
                    ),
                    (
                        "coverage-${version}-cp${py_version}-*-win_amd64.whl",
                        {
                            "platforms": ["windows-x64"],
                            "python_versions": ["3.3"]
                        }
                    )
                ],
                [
                    {
                        "date": "2019-07-29 15:29:28",
                        "version": "4.5.4",
                        "url": "https://files.pythonhosted.org/packages"
                               "/3b/2f/c641609b79e292a4a29375c4af0cf8156c36a0613000513b05eb1a838a59"
                               "/coverage-4.5.4-cp33-cp33m-macosx_10_10_x86_64.whl",
                        "sha256": "6b62544bb68106e3f00b21c8930e83e584fdca005d4fffd29bb39fb3ffa03cb5",
                        "platforms": ["osx-x64"],
                        "python_versions": ["3.3"],
                    },
                    {
                        "date": "2016-07-26 21:09:17",
                        "version": "4.2",
                        "url": "https://files.pythonhosted.org/packages"
                               "/b1/55/02815cb8abb091033abb979ebde5122bb33b85c5987dede9ccd019033d19"
                               "/coverage-4.2-cp33-cp33m-win_amd64.whl",
                        "sha256": "bd4eba631f07cae8cdb9c55c144f165649e6701b962f9d604b4e00cf8802406c",
                        "platforms": ["windows-x64"],
                        "python_versions": ["3.3"],
                    }
                ]
            ),
            (
                "py33_arrow_latest",
                {"max_releases": 1},
                "https://pypi.org/project/arrow",
                [
                    (
                        "arrow-*-py2.py3-none-any.whl",
                        {
                            "python_versions": ["3.3"]
                        }
                    )
                ],
                [
                    {
                        "date": "2019-06-04 14:00:29",
                        "version": "0.14.2",
                        "url": "https://files.pythonhosted.org/packages"
                               "/a2/6a/a3d20e80ee4fee7c55c022fb28d52239bd01171edd3c137dd1e2ef8b2a20"
                               "/arrow-0.14.2-py2.py3-none-any.whl",
                        "sha256": "03404b624e89ac5e4fc19c52045fa0f3203419fd4dd64f6e8958c522580a574a",
                        "python_versions": ["3.3"]
                    },
                ]
            ),
        ),
        first_param_name_suffix=True
    )
    def download_info_from_releases(self, extra_settings, url, asset_templates, result):
        client = PyPiClient(self.settings(extra_settings))
        self.assertEqual(result, client.download_info_from_releases(url, asset_templates))
