import re

from ..clients.github_client import GitHubClient
from ..downloaders.downloader_exception import DownloaderException
from .base_provider import BaseProvider
from .provider_exception import (
    GitProviderDownloadInfoException,
    GitProviderRepoInfoException,
)


class GitHubProvider(BaseProvider):
    """
    Allows using a public GitHub repository as the source for a single package.
    For legacy purposes, this can also be treated as the source for a Package
    Control "repository".

    :param url:
        The public web URL to the GitHub repository. Should be in the format
        `https://github.com/user/package` for the master branch, or
        `https://github.com/user/package/tree/{branch_name}` for any other
        branch.

    :param settings:
        A dict containing configuration for providers and http clients:
        - `debug`
        - `package_name_map`
        - `http_basic_auth`
        - `cache_length`
        - `timeout`
        - `http_proxy`
        - `proxy_username`
        - `proxy_password`
    """

    def __init__(self, url, settings):
        # Clean off the trailing .git to be more forgiving
        super().__init__(re.sub(r"\.git$", "", url), settings)

    @classmethod
    def match_url(cls, url):
        """
        Indicates if this provider can handle the provided url

        :param url:
            The URL to the repository, in one of the forms:
                https://github.com/{user}/{repo}.git
                https://github.com/{user}/{repo}
                https://github.com/{user}/{repo}/
                https://github.com/{user}/{repo}/tree/{branch}
                https://github.com/{user}/{repo}/tree/{branch}/

        :return:
            True if url matches an supported scheme.
        """
        user, repo, _ = GitHubClient.user_repo_branch(url)
        return bool(user and repo)

    def _fetch(self):
        """
        Fetch package meta data from GitHub API
        """
        client = GitHubClient(self.settings)

        try:
            repo_info = client.repo_info(self.url)
            if not repo_info:
                raise GitProviderRepoInfoException(self)

            downloads = client.download_info_from_branch(self.url, repo_info["default_branch"])
            if not downloads:
                raise GitProviderDownloadInfoException(self)

            for download in downloads:
                download["sublime_text"] = "*"
                download["platforms"] = ["*"]

            name = repo_info["name"]
            name = self.settings.get("package_name_map", {}).get(name, name)
            self.packages[name] = {
                "name": name,
                "description": repo_info["description"],
                "homepage": repo_info["homepage"],
                "author": repo_info["author"],
                "last_modified": downloads[0].get("date"),
                "releases": downloads,
                "previous_names": [],
                "labels": [],
                "source": self.url,
                "readme": repo_info["readme"],
                "issues": repo_info["issues"],
                "donate": repo_info["donate"],
            }

        except DownloaderException as e:
            self.failed_sources[self.url] = e
            self.packages = {}
