import json

from ..download_manager import http_get, resolve_url, update_url
from .bitbucket_provider import BitBucketProvider
from .github_provider import GitHubProvider
from .gitlab_provider import GitLabProvider
from .provider_exception import InvalidChannelFileException, ProviderException
from .repository_provider import RepositoryProvider
from .schema_version import SchemaVersion


def channel_provider_for(url, settings):
    for provider_class in [ChannelProvider]:
        if provider_class.match_url(url):
            return provider_class(url, settings)
    return None


def repo_provider_for(url, settings):
    for provider_class in (BitBucketProvider, GitHubProvider, GitLabProvider, RepositoryProvider):
        if provider_class.match_url(url):
            return provider_class(url, settings)
    return None


class ChannelProvider(RepositoryProvider):
    """
    A provider for package and library records from package control channels.

    A channel represents a list of repositories.

    A repository can be any source supported by a `BaseProvider`
    subclass. Most commonly, it is a json file with metadata about packages and
    libraries. Metadata provide information about how to retrieve version
    information and download assets.

    Up to this point a channel is equal to a json repository with `"includes"`,
    except it using `"repositories"` key instead.

    What makes a channel unique are its...

    1. ability to list code hoster repositories via GitHubRepository etc.
    2. `packages_cache` and `libraries_cache` dictionaries, which contain lists
       of resolved package and library metadata for each listed repository. A
       resolved package/library exclusively provides release information with
       "version" and "url" keys for direct download.

    Those are most commonly provided by a crawler application to avoid each
    client individually reaching out to code hosters to get required data for
    all packages.

    Note: Cached meta data are untrusted and thus sanetized and validated by
    RepositoryProvider's methods for security reasons.

    If `"repositories"` list contains unresolved package information, Package
    Control can fallback to them in order to retrieve a full list of available
    versions for individual packages on demand.

    :param url:
        The URL of the channel

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

    def _fetch(self):
        """
        Retrieves and loads the JSON for other methods to use

        :raises:
            InvalidChannelFileException: when parsing or validation file content fails
            ProviderException: when an error occurs trying to open a file
            DownloaderException: when an error occurs trying to open a URL
        """
        json_string = http_get(self.url, self.settings, "Error downloading channel.")

        try:
            content = json.loads(json_string.decode("utf-8"))
        except ValueError:
            raise InvalidChannelFileException(self, "parsing JSON failed.")
        else:
            self._parse(content)

    def _parse(self, content):
        try:
            schema_version = SchemaVersion(content["schema_version"])
        except KeyError:
            raise InvalidChannelFileException(self, 'the "schema_version" JSON key is missing.')
        except ValueError as e:
            raise InvalidChannelFileException(self, e)

        if "repositories" not in content:
            raise InvalidChannelFileException(self, 'the "repositories" JSON key is missing.')

        repo_urls = content["repositories"]
        if not isinstance(repo_urls, list):
            raise InvalidChannelFileException(self, '"repositories" must be a list.')

        if schema_version.major < 3:
            libs = {}
            pkgs = content.get("packages_cache", {})
            migrate_lib = self._normalize_library
            migrate_pkg = self._migrate_package_from_v2
        elif schema_version.major < 4:
            libs = content.get("dependencies_cache", {})
            pkgs = content.get("packages_cache", {})
            migrate_lib = self._migrate_library_from_v3
            migrate_pkg = self._migrate_package_from_v3
        else:
            libs = content.get("libraries_cache", {})
            pkgs = content.get("packages_cache", {})
            migrate_lib = self._normalize_library
            migrate_pkg = self._normalize_package

        debug = self.settings.get("debug", False)

        # fetch uncached repositories
        repo_providers = {}
        for repo_url in repo_urls:
            if repo_url not in libs and repo_url not in pkgs:
                repo_provider = repo_provider_for(
                    update_url(resolve_url(self.url, repo_url), debug), self.settings
                )
                if repo_provider:
                    repo_providers[repo_url] = repo_provider
                else:
                    self.failed_sources[repo_url] = ProviderException(
                        "{} is not a supported repository.".format(repo_url)
                    )

        # todo: run in parallel
        for repo_provider in repo_providers.values():
            repo_provider.fetch()

        # merge in strict order
        for repo_url in reversed(repo_urls):
            if repo_url in repo_providers:
                self.update(repo_providers[repo_url])
            else:
                updated_repo_url = update_url(repo_url, debug)
                for lib in filter(None, map(migrate_lib, libs.get(repo_url, []))):
                    lib["source"] = updated_repo_url
                    self.libraries[lib["name"]] = lib
                for pkg in filter(None, map(migrate_pkg, pkgs.get(repo_url, []))):
                    pkg["source"] = updated_repo_url
                    self.packages[pkg["name"]] = pkg
