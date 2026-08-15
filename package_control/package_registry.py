import sublime
import threading

from . import __version__, library
from .console_write import console_write
from .download_manager import update_url
from .package_version import PackageVersion, version_sort
from .pep440 import PEP440Version
from .providers import channel_provider_for, repo_provider_for
from .providers.provider_exception import ProviderException
from .selectors import is_compatible_platform, is_compatible_python, is_compatible_version

DEFAULT_CHANNEL = "https://packagecontrol.io/channel_v3.json"
OLD_DEFAULT_CHANNELS = {
    "https://packagecontrol.io/channel.json",
    "https://sublime.wbond.net/channel.json",
    "https://sublime.wbond.net/repositories.json",
}

STATE_IDLE = 0
STATE_FETCHING = 1
STATE_FETCHED = 2
STATE_FAILED = 3


class PackageRegistry:
    """
    A collection of packages and libraries

    Aggregates packages and libraries from all specified `Provider` instances,
    such as channels and repositories.

    :param settings:
        A dict containing configuration for providers and http clients:
        - `channels`
        - `repositories`

        downloader/provider specific:
        - `debug`
        - `package_name_map`
        - `http_basic_auth`
        - `cache_length`
        - `timeout`
        - `http_proxy`
        - `proxy_username`
        - `proxy_password`
    """

    __slots__ = [
        "libraries",
        "lock",
        "packages",
        "renamed_packages",
        "settings",
        "state",
        "unavailable_libraries",
        "unavailable_packages",
    ]

    def __init__(self, settings):
        self.lock = threading.Lock()
        self.state = STATE_IDLE
        self.settings = settings
        self.libraries = {}
        self.packages = {}
        self.renamed_packages = {}
        self.unavailable_libraries = set()
        self.unavailable_packages = set()

    def ensure_fetched(self):
        """
        Check state flag to fetch channels and repositories on demand.

        The method ensures only the first of concurrently scheduled tasks
        (e.g. via asyncio.gather()) actually executes fetch() and the others
        just wait for its completion.
        """
        if self.state != STATE_FETCHED:
            with self.lock:
                if self.state == STATE_IDLE:
                    self.fetch()

    def fetch(self):
        """
        Fetch channels and repositories and set state flag accordingly.
        """
        self.state = STATE_FETCHING
        try:
            self._fetch()
        except BaseException:
            self.state = STATE_FAILED
            raise
        else:
            self.state = STATE_FETCHED

    def _fetch(self):
        providers = []
        failed_sources = {}

        debug = self.settings.get("debug", False)
        if debug:
            import time

            start_time = time.time()

            console_write(
                """
                Fetching list of available packages and libraries
                  Platform: %s-%s
                  Sublime Text Version: %s
                  Package Control Version: %s
                """,
                (
                    sublime.platform(),
                    sublime.arch(),
                    sublime.version(),
                    __version__,
                ),
            )

        found_default = False

        for url in reversed(self.settings.get("channels", [])):
            if url in OLD_DEFAULT_CHANNELS:
                if found_default:
                    continue
                found_default = True
                url = DEFAULT_CHANNEL

            provider = channel_provider_for(update_url(url, False), self.settings)
            if provider:
                providers.append(provider)
            else:
                failed_sources[url] = ProviderException(
                    "{} is not a supported channel.".format(url)
                )

        for url in reversed(self.settings.get("repositories", [])):
            provider = repo_provider_for(update_url(url, False), self.settings)
            if provider:
                providers.append(provider)
            else:
                failed_sources[url] = ProviderException(
                    "{} is not a supported repository.".format(url)
                )

        # run in parallel
        # todo: run in parallel
        for provider in providers:
            provider.fetch()

        # merge in strict order
        broken_libraries = {}
        broken_packages = {}
        libraries = {}
        packages = {}
        for provider in providers:
            for name, lib in provider.libraries.items():
                # Convert legacy dependency names to official pypi package names.
                # This is required for forward compatibility with upcomming changes
                # in scheme 4.0.0. Do it here to apply only on client side.
                name = lib["name"] = library.translate_name(name)
                dist_name = library.escape_name(name).lower()
                libraries[dist_name] = lib

            if provider.packages:
                packages.update(provider.packages)
            if provider.broken_libraries:
                broken_libraries.update(provider.broken_libraries)
            if provider.broken_packages:
                broken_packages.update(provider.broken_packages)
            if provider.failed_sources:
                failed_sources.update(provider.failed_sources)

        # filter and sort supported libraries
        supported_libraries = {}
        unavailable_libraries = set()
        for name, lib in sorted(libraries.items()):
            lib["releases"] = self._compatible_library_releases(lib["releases"])
            if lib["releases"]:
                supported_libraries[name] = lib
            else:
                unavailable_libraries.add(name)

        # filter and sort supported packages
        supported_packages = {}
        unavailable_packages = set()
        for name, pkg in sorted(packages.items()):
            pkg["releases"] = self._compatible_package_releases(name, pkg["releases"])
            if pkg["releases"]:
                supported_packages[name] = pkg
            else:
                unavailable_packages.add(name)

        # determine renamed packages
        renamed_packages = {}
        for package in self.packages.values():
            if "previous_names" not in package:
                continue

            previous_names = package["previous_names"]
            if not isinstance(previous_names, list):
                previous_names = [previous_names]

            for previous_name in previous_names:
                renamed_packages[previous_name] = package["name"]

        # print stats to console
        if debug:
            msg = "Fetched {} packages and {} libraries in {:.3f}s."
            msg = msg.format(len(packages), len(libraries), time.time() - start_time)
            if broken_packages:
                msg += "\n  {} broken packages dropped.".format(len(broken_packages))
                for name, exc in sorted(broken_packages.items()):
                    msg += "\n  - {}: {}".format(name, exc)
            if unavailable_packages:
                msg += "\n  {} incompatible packages dropped.".format(len(unavailable_packages))
                msg += "\n    " + ", ".join(sorted(unavailable_packages))
            if broken_libraries:
                msg += "\n  {} broken libraries dropped.".format(len(broken_libraries))
                for name, exc in sorted(broken_libraries.items()):
                    msg += "\n  - {}: {}".format(name, exc)
            if unavailable_libraries:
                msg += "\n  {} incompatible libraries dropped.".format(len(unavailable_libraries))
                msg += "\n    " + ", ".join(sorted(unavailable_libraries))
            if failed_sources:
                msg += "\n  {} sources failed downloading.".format(len(failed_sources))
                for name, exc in sorted(failed_sources.items()):
                    msg += "\n  - {}: {}".format(name, exc)
            console_write(msg)

        # apply results
        self.unavailable_libraries = unavailable_libraries
        self.unavailable_packages = unavailable_packages
        self.renamed_packages = renamed_packages
        self.libraries = supported_libraries
        self.packages = supported_packages

    def get_libraries(self):
        """
        A list of library records provided by this repository.

        :return:
            A sorted list of raw or resolved library records.

            ```py
            {
                'name': name,
                'author': author,
                'description': description,
                'issues': URL,
                'releases': [
                    {
                        'url': url,
                        'date': date,
                        'version': version,
                        'platforms': [platform name, ...],
                        'python_versions': ['3.3', '3.8'],
                        'sublime_text': compatible version,
                        'sha256': hex hash
                    }, ...
                ],
                'source': url,
            }
            ```
        """
        self.ensure_fetched()
        return sorted(self.libraries.values(), key=lambda lib: lib["name"].lower())

    def get_library(self, name):
        """
        The record for specified library provided by this repository.

        :return:
            Raw or resolved library record.

            ```py
            {
                'name': name,
                'author': author,
                'description': description,
                'issues': URL,
                'releases': [
                    {
                        'url': url,
                        'date': date,
                        'version': version,
                        'platforms': [platform name, ...],
                        'python_versions': ['3.3', '3.8'],
                        'sublime_text': compatible version,
                        'sha256': hex hash
                    }, ...
                ],
                'source': url,
            }
            ```
        """
        self.ensure_fetched()
        return self.libraries.get(name)

    def get_libray_names(self):
        """
        A set of available library names in the registry
        """
        self.ensure_fetched()
        return set(self.libraries.keys())

    def get_packages(self):
        """
        A list of package records provided by this repository.

        :return:
            A sorted list of raw or resolved package records.

            ```py
            {
                'name': name,
                'author': author,
                'description': description,
                'issues': url,
                'homepage': homepage,
                'readme': url,
                'donate': url,
                'labels': [label, ...],
                'previous_names': [old_name, ...],
                'last_modified': last modified date,
                'releases': [
                    {
                        'url': url,
                        'date': date,
                        'version': version,
                        'platforms': [platform name, ...],
                        'sublime_text': compatible version,
                        'libraries': [library name, ...]
                    }, ...
                ],
                'source': url,
            }
            ```
        """
        self.ensure_fetched()
        return sorted(self.packages.values(), key=lambda pkg: pkg["name"].lower())

    def get_package(self, name):
        """
        The record for specified package provided by this repository.

        If `name` is a previous name of a renamed package, return latest
        available record.

        :return:
            Raw or resolved package record.

            ```py
            {
                'name': name,
                'author': author,
                'description': description,
                'issues': url,
                'homepage': homepage,
                'readme': url,
                'donate': url,
                'labels': [label, ...],
                'previous_names': [old_name, ...],
                'last_modified': last modified date,
                'releases': [
                    {
                        'url': url,
                        'date': date,
                        'version': version,
                        'platforms': [platform name, ...],
                        'sublime_text': compatible version,
                        'libraries': [library name, ...]
                    }, ...
                ],
                'source': url,
            }
            ```
        """
        self.ensure_fetched()
        return self.packages.get(self.renamed_packages.get(name, name))

    def get_package_names(self):
        """
        A set of available package names in the registry
        """
        self.ensure_fetched()
        return set(self.packages.keys())

    def _compatible_library_releases(self, releases):
        """
        Determine newest release compatible with the current platform,
        python_version and version of Sublime Text

        Note: Currently, drops raw releases, which do not provide an "url".

        :param releases:
            A list of release dicts

        :return:
            A list of release dicts sorted by version in decending order
        """
        compatible_releases = version_sort(
            (
                release
                for release in releases
                if "url" in release
                and is_compatible_platform(release["platforms"])
                and is_compatible_python(release["python_versions"])
                and is_compatible_version(release["sublime_text"])
                and PEP440Version(release["version"]).is_final
            ),
            reverse=True,
        )
        return compatible_releases

    def _compatible_package_releases(self, package_name, releases):
        """
        Determine newest release compatible with the current platform and
        version of Sublime Text

        Note: Currently, drops raw releases, which do not provide an "url".

        :param package_name:
            The name of the package

        :param releases:
            A list of release dicts

        :return:
            A list of release dicts sorted by version in decending order
        """

        install_prereleases = self.settings.get("install_prereleases")
        allow_prereleases = (
            install_prereleases is True
            or isinstance(install_prereleases, list)
            and package_name in install_prereleases
        )

        compatible_releases = version_sort(
            (
                release
                for release in releases
                if "url" in release
                and is_compatible_platform(release["platforms"])
                and is_compatible_version(release["sublime_text"])
                and (allow_prereleases or PackageVersion(release["version"]).is_final)
            ),
            reverse=True,
        )
        return compatible_releases
