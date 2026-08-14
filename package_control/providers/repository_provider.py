import json
from urllib.parse import urlparse

from ..download_manager import http_get, resolve_url, update_url
from .base_provider import BaseProvider
from .provider_exception import (
    InvalidRepoFileException,
    ProviderException,
)
from .schema_version import SchemaVersion

library_template = {
    "name": None,
    "description": None,
    "author": None,
    "issues": None,
    "releases": [],
    "source": None,
}

package_template = {
    "details": None,
    "name": None,
    "description": None,
    "author": None,
    "issues": None,
    "homepage": None,
    "readme": None,
    "donate": None,
    "labels": [],
    "releases": [],
    "previous_names": [],
    "last_modified": None,
    "source": None,
}

allowed_raw_release_keys = {
    "asset",
    "base",
    "branch",
    "libraries",
    "platforms",
    "python_versions",
    "sublime_text",
    "tags",
}

allowed_url_release_keys = {
    "date",
    "libraries",
    "platforms",
    "python_versions",
    "sha256",
    "sublime_text",
    "url",
    "version",
}


def normalize(dic, template):
    return {key: dic.get(key, value) for key, value in template.items()}


def keep_only(dic, allowed_keys):
    for k in tuple(dic.keys()):
        if k not in allowed_keys:
            del dic[k]
    return dic


def latest_release_date(releases):
    # assumes first release to be the latest one
    for release in releases:
        if "date" in release:
            return release["date"]


class RepositoryProvider(BaseProvider):
    """
    Generic repository downloader that fetches package info

    With the current channel/repository architecture where the channel file
    caches info from all includes repositories, these package providers just
    serve the purpose of downloading packages not in the default channel.

    The structure of the JSON a repository should contain is located in
    example-packages.json.

    :param url:
        The URL of the package repository

    :param settings:
        A dict containing configuration for providers and http clients:
        - `debug`
        - `http_basic_auth`
        - `cache_length`
        - `timeout`
        - `http_proxy`
        - `proxy_username`
        - `proxy_password`
    """

    __slots__ = ["included_urls"]

    def __init__(self, url, settings):
        super().__init__(url, settings)
        self.included_urls = set()

    def get_renamed_packages(self):
        """:return: A dict of the packages that have been renamed"""

        self.ensure_fetched()

        output = {}
        for package in self.packages.values():
            if "previous_names" not in package:
                continue

            previous_names = package["previous_names"]
            if not isinstance(previous_names, list):
                previous_names = [previous_names]

            for previous_name in previous_names:
                output[previous_name] = package["name"]

        return output

    def _fetch(self):
        """
        Fetches the contents of a URL of file path

        :raises:
            ProviderException: when an error occurs trying to open a file
            DownloaderException: when an error occurs trying to open a URL
        """

        # Prevent circular includes
        if self.url in self.included_urls:
            raise ProviderException('Error, repository "{}" already included.'.format(self.url))

        self.included_urls.add(self.url)

        json_string = http_get(self.url, self.settings, "Error downloading repository.")

        try:
            content = json.loads(json_string.decode("utf-8"))
        except ValueError:
            raise InvalidRepoFileException(self, "parsing JSON failed.") from None
        else:
            self._parse(content)

    def _parse(self, content):
        try:
            schema_version = content["schema_version"] = SchemaVersion(content["schema_version"])
        except KeyError:
            raise InvalidRepoFileException(
                self, 'the "schema_version" JSON key is missing.'
            ) from None
        except ValueError:
            raise InvalidRepoFileException(self, "parsing JSON failed.") from None

        # Main keys depending on scheme version
        if schema_version.major < 4:
            repo_keys = {"packages", "dependencies", "includes"}
        else:
            repo_keys = {"packages", "libraries", "includes"}

        # Check existence of at least one required main key
        if not set(content.keys()) & repo_keys:
            raise InvalidRepoFileException(self, "it doesn't look like a repository.")

        # Check type of existing main keys
        for key in repo_keys:
            if key not in content:
                content[key] = []
            elif not isinstance(content[key], list):
                raise InvalidRepoFileException(self, 'the "{}" key is not an array.'.format(key))

        # Allow repositories to include other repositories, recursively
        repo_providers = []
        for include_url in reversed(content["includes"]):
            repo_provider = RepositoryProvider(
                update_url(resolve_url(self.url, include_url), False), self.settings
            )
            if repo_provider:
                repo_provider.included_urls = self.included_urls
                repo_providers.append(repo_provider)
            else:
                self.failed_sources[include_url] = ProviderException(
                    "{} is not a supported repository.".format(include_url)
                )

        # todo: run in parallel
        for repo_provider in repo_providers:
            repo_provider.fetch()

        # merge in strict order
        for repo_provider in repo_providers:
            self.update(repo_provider)

        # add inline packages and libaries
        if schema_version.major < 3:
            libs = []
            pkgs = content.get("packages", [])
            migrate_lib = self._normalize_library
            migrate_pkg = self._migrate_package_from_v2
        elif schema_version.major < 4:
            libs = content.get("dependencies", [])
            pkgs = content.get("packages", [])
            migrate_lib = self._migrate_library_from_v3
            migrate_pkg = self._migrate_package_from_v3
        else:
            libs = content.get("libraries", [])
            pkgs = content.get("packages", [])
            migrate_lib = self._normalize_library
            migrate_pkg = self._normalize_package

        for lib in filter(None, map(migrate_lib, libs)):
            lib["source"] = self.url
            self.libraries[lib["name"]] = lib

        for pkg in filter(None, map(migrate_pkg, pkgs)):
            pkg["source"] = self.url
            self.packages[pkg["name"]] = pkg

    def _migrate_library_from_v3(self, lib):
        """
        Inplace migrate supplied library record and varify it.

        Assumes source record to be discarded anyway, as the method is part of loading a repo.

        :returns:
            Migrated and verified library record.
            None, if record is invalid.
        """
        if "load_order" in lib:
            del lib["load_order"]

        for release in lib["releases"]:
            release["python_versions"] = ["3.3"]

        return self._normalize_library(lib)

    def _normalize_library(self, lib):
        """
        Verify and add missing keys to supplied library record.

        Assumes source record to be discarded anyway, as the method is part of loading a repo.

        :returns:
            Normalized and verified library record.
            None, if record is invalid.
        """
        if "name" not in lib:
            id = len(self.broken_libraries)
            exc = ProviderException('No "name" specified!')
            self.broken_libraries["unknown-{}".format(id)] = exc
            return None

        valid_releases = []
        for release in lib.get("releases", []):
            # drop malformed releases
            if "url" in release and "version" in release:
                release["url"] = resolve_url(self.url, release["url"])
                keep_only(release, allowed_url_release_keys)
                if "date" not in release:
                    release["date"] = "1970-01-01 00:00:00"

            elif "base" in release:
                release["base"] = resolve_url(self.url, release["base"])
                keep_only(release, allowed_raw_release_keys)

            else:
                continue

            # add defaults
            if "platforms" not in release:
                release["platforms"] = ["*"]
            elif isinstance(release["platforms"], str):
                release["platforms"] = [release["platforms"]]
            if "python_versions" not in release:
                release["python_versions"] = ["3.3"]
            if "sublime_text" not in release:
                release["sublime_text"] = "*"

            valid_releases.append(release)

        if not valid_releases:
            exc = ProviderException("No valid release branch!")
            self.broken_libraries[lib["name"]] = exc
            return None

        lib["releases"] = valid_releases

        if "last_modified" not in lib:
            lib["last_modified"] = latest_release_date(valid_releases)

        return normalize(lib, library_template)

    def _migrate_package_from_v2(self, pkg):
        """
        Inplace migrate supplied package record and varify it.

        Assumes source record to be discarded anyway, as the method is part of loading a repo.

        :returns:
            Migrated and verified package record.
            None, if record is invalid.
        """
        if "releases" not in pkg:
            pkg["releases"] = []

        valid_releases = []
        for release in pkg.get("releases", []):
            # add default sublime text version specifier
            if "sublime_text" not in release:
                release["sublime_text"] = "<3000"

            # rename 'details' to 'base', if present
            base = release.pop("details", None)
            if base is not None:
                url = urlparse(base)
                parts = url.path.split("/")[1:]  # strip first empty part

                # invalid url, needs at least /user/repo
                if len(parts) < 2:
                    continue

                if "github" in url.hostname:
                    # migrate https://github.com/user/repo/tags
                    # Note: tag-prefixes are not supported.
                    if len(parts) > 2 and parts[2] == "tags":
                        release["tags"] = True

                    # migrate https://github.com/user/repo/tree/{branch}
                    elif len(parts) > 3 and parts[2] == "tree":
                        release["branch"] = parts[3]

                    # stripped url if differs from global details item
                    base = "{scheme}://{hostname}/{user}/{repo}".format(
                        scheme=url.scheme, hostname=url.hostname, user=parts[0], repo=parts[1]
                    )
                    if base != pkg.get("details"):
                        release["base"] = base

                elif "bitbucket" in url.hostname:
                    # migrate https://github.com/user/repo#tags
                    # Note: tag-prefixes are not supported.
                    if url.fragment == "tags":
                        release["tags"] = True

                    # migrate https://github.com/user/repo/src/{branch}
                    elif len(parts) > 3 and parts[2] == "src":
                        release["branch"] = parts[3]

                    # stripped url if differs from global details item
                    base = "{scheme}://{hostname}/{user}/{repo}".format(
                        scheme=url.scheme, hostname=url.hostname, user=parts[0], repo=parts[1]
                    )
                    if base != pkg.get("details"):
                        release["base"] = base

                else:
                    release["base"] = base

            valid_releases.append(release)

        pkg["releases"] = valid_releases

        return self._normalize_package(pkg)

    def _migrate_package_from_v3(self, pkg):
        """
        Inplace migrate supplied package record and varify it.

        Assumes source record to be discarded anyway, as the method is part of loading a repo.

        :returns:
            Migrated and verified package record.
            None, if record is invalid.
        """
        if "releases" in pkg:
            # schema v3 releases may specify dependencies, convert to libraries
            for release in pkg["releases"]:
                if "dependencies" in release:
                    release["libraries"] = release.pop("dependencies", [])

        return self._normalize_package(pkg)

    def _normalize_package(self, pkg):
        """
        Verify and add missing keys to supplied package record.

        Assumes source record to be discarded anyway, as the method is part of loading a repo.

        :returns:
            Normalized and verified package record.
            None, if record is invalid.
        """
        details_url = pkg.get("details", "")

        if not pkg.get("name"):
            # resolve missing or empty name from code hoster's repository name
            # url of form https://host/user/repo
            try:
                url = urlparse(details_url)
                pkg["name"] = url.path.split("/")[2]
            except IndexError:
                id = len(self.broken_packages)
                exc = ProviderException('Neither "name" nor "details" specified!')
                self.broken_packages["unknown-{}".format(id)] = exc
                # unable to resolve package name, skip it
                return None

        valid_releases = []
        for release in pkg.get("releases", []):
            # drop malformed releases
            if "url" in release and "version" in release:
                release["url"] = resolve_url(self.url, release["url"])
                keep_only(release, allowed_url_release_keys)
                if "date" not in release:
                    release["date"] = "1970-01-01 00:00:00"

            elif "base" in release:
                release["base"] = resolve_url(self.url, release["base"])
                keep_only(release, allowed_raw_release_keys)

            elif details_url:
                keep_only(release, allowed_raw_release_keys)

            else:
                continue

            # add some defaults
            if "platforms" not in release:
                release["platforms"] = ["*"]
            elif isinstance(release["platforms"], str):
                release["platforms"] = [release["platforms"]]
            if "sublime_text" not in release:
                release["sublime_text"] = "*"

            valid_releases.append(release)

        if not valid_releases:
            exc = ProviderException("No valid release branch!")
            self.broken_packages[pkg["name"]] = exc
            return None

        pkg["releases"] = valid_releases

        if "last_modified" not in pkg:
            pkg["last_modified"] = latest_release_date(valid_releases)

        return normalize(pkg, package_template)
