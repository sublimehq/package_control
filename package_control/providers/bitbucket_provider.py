from ..clients.bitbucket_client import BitBucketClient
from ..downloaders.downloader_exception import DownloaderException
from .base_provider import BaseProvider
from .provider_exception import (
    GitProviderDownloadInfoException,
    GitProviderRepoInfoException,
)


class BitBucketProvider(BaseProvider):
    """
    Allows using a public BitBucket repository as the source for a single package.
    For legacy purposes, this can also be treated as the source for a Package
    Control "repository".

    :param repo:
        The public web URL to the BitBucket repository. Should be in the format
        `https://bitbucket.org/user/package`.

    :param settings:
        A dict containing at least the following fields:
          `cache_length`,
          `debug`,
          `timeout`,
          `user_agent`
        Optional fields:
          `http_proxy`,
          `https_proxy`,
          `proxy_username`,
          `proxy_password`,
          `query_string_params`,
          `http_basic_auth`
    """

    @classmethod
    def match_url(cls, repo_url):
        """
        Indicates if this provider can handle the provided repo_url

        :param repo_url:
            The URL to the repository, in one of the forms:
                https://bitbucket.org/{user}/{repo}.git
                https://bitbucket.org/{user}/{repo}
                https://bitbucket.org/{user}/{repo}/
                https://bitbucket.org/{user}/{repo}/src/{branch}
                https://bitbucket.org/{user}/{repo}/src/{branch}/

        :return:
            True if repo_url matches an supported scheme.
        """
        user, repo, _ = BitBucketClient.user_repo_branch(repo_url)
        return bool(user and repo)

    def get_packages(self):
        """
        Uses the BitBucket API to construct necessary info for a package

        :return:
            A generator of

            ```py
            {
                'name': name,
                'description': description,
                'author': author,
                'homepage': homepage,
                'previous_names': [old_name, ...],
                'labels': [label, ...],
                'sources': [url, ...],
                'readme': url,
                'issues': url,
                'donate': url,
                'buy': url,
                'last_modified': last modified date,
                'releases': [
                    {
                        'sublime_text': compatible version,
                        'platforms': [platform name, ...],
                        'url': url,
                        'date': date,
                        'version': version,
                        'libraries': [library name, ...]
                    }, ...
                ]
            }
            ```

            dictionaries
        """

        if self.packages is not None:
            for details in self.packages.values():
                yield details
            return

        client = BitBucketClient(self.settings)

        try:
            repo_info = client.repo_info(self.repo_url)
            if not repo_info:
                raise GitProviderRepoInfoException(self)

            downloads = client.download_info_from_branch(self.repo_url, repo_info['default_branch'])
            if not downloads:
                raise GitProviderDownloadInfoException(self)

            for download in downloads:
                download['sublime_text'] = '*'
                download['platforms'] = ['*']

            name = repo_info['name']
            details = {
                'name': name,
                'description': repo_info['description'],
                'homepage': repo_info['homepage'],
                'author': repo_info['author'],
                'last_modified': downloads[0].get('date'),
                'releases': downloads,
                'previous_names': [],
                'labels': [],
                'sources': [self.repo_url],
                'readme': repo_info['readme'],
                'issues': repo_info['issues'],
                'donate': repo_info['donate'],
                'buy': None
            }
            self.packages = {name: details}
            yield details

        except DownloaderException as e:
            self.failed_sources[self.repo_url] = e
            self.packages = {}
