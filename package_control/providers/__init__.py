from .bitbucket_provider import BitBucketProvider
from .github_provider import GitHubProvider
from .gitlab_provider import GitLabProvider
from .repository_provider import RepositoryProvider

from .channel_provider import ChannelProvider


REPOSITORY_PROVIDERS = [
    BitBucketProvider,
    GitHubProvider,
    GitLabProvider,
    RepositoryProvider,
]

CHANNEL_PROVIDERS = [ChannelProvider]


def channel_provider_for(url, settings):
    for provider_class in CHANNEL_PROVIDERS:
        if provider_class.match_url(url):
            return provider_class(url, settings)
    return None


def repo_provider_for(url, settings):
    for provider_class in REPOSITORY_PROVIDERS:
        if provider_class.match_url(url):
            return provider_class(url, settings)
    return None
