import threading

from ..downloaders.downloader_exception import DownloaderException

STATE_IDLE = 0
STATE_FETCHING = 1
STATE_FETCHED = 2
STATE_FAILED = 3


class BaseProvider:
    """
    Base repository downloader that fetches package info

    This base class acts as interface to ensure all providers expose the same
    set of methods. All providers should therefore derive from this base class.

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

    __slots__ = [
        "broken_libraries",
        "broken_packages",
        "failed_sources",
        "libraries",
        "lock",
        "packages",
        "settings",
        "state",
        "url",
    ]

    def __init__(self, url, settings):
        self.lock = threading.Lock()
        self.state = STATE_IDLE
        self.broken_libraries = {}
        self.broken_packages = {}
        self.failed_sources = {}
        self.libraries = {}
        self.packages = {}
        self.url = url
        self.settings = settings

    def update(self, other):
        """
        Update this instance's records with those from another provider.

        :param other:
            The `BaseProvider` instance to get new records from.
        """
        if other.broken_libraries:
            self.broken_libraries.update(other.broken_libraries)
        if other.broken_packages:
            self.broken_packages.update(other.broken_packages)
        if other.failed_sources:
            self.failed_sources.update(other.failed_sources)
        if other.libraries:
            self.libraries.update(other.libraries)
        if other.packages:
            self.packages.update(other.packages)

    @classmethod
    def match_url(cls, url):
        """
        Indicates if this provider can handle the provided url
        """
        return True

    def ensure_fetched(self):
        """
        Check state flag to fetch data on demand.

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
        Fetch and load data from specified url and set state flag accordingly.
        """
        self.state = STATE_FETCHING
        try:
            self._fetch()
        except DownloaderException as exc:
            self.failed_sources[self.url] = exc
            self.state = STATE_FAILED
        except BaseException as exc:
            self.failed_sources[self.url] = exc
            self.state = STATE_FAILED
            raise
        else:
            self.state = STATE_FETCHED

    def _fetch(self):
        """
        Retrieves and loads the JSON for other methods to use

        :raises:
            NotImplementedError: when called
        """
        raise NotImplementedError()

    def get_broken_libraries(self):
        """
        List of library names for libraries that are missing information

        :return:
            A generator of ("Library Name", Exception()) tuples
        """
        self.ensure_fetched()
        return self.broken_libraries.items()

    def get_broken_packages(self):
        """
        List of package names for packages that are missing information

        :return:
            A generator of ("Package Name", Exception()) tuples
        """
        self.ensure_fetched()
        return self.broken_packages.items()

    def get_failed_sources(self):
        """
        List of any URLs that could not be accessed while accessing this repository

        :return:
            A generator of ("https://example.com", Exception()) tuples
        """
        self.ensure_fetched()
        return self.failed_sources.items()

    def get_libraries(self):
        """
        A list of library records provided by this repository.

        :return:
            A sorted list of library records.

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

    def get_renamed_packages(self):
        """For API-compatibility with RepositoryProvider"""
        return {}
