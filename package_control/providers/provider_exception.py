from ..downloaders.downloader_exception import DownloaderException


class ProviderException(DownloaderException):
    """If a provider could not return information"""


class InvalidChannelFileException(ProviderException):

    def __init__(self, provider, reason_message):
        self.reason_message = reason_message
        self.url = provider.url

    def __str__(self):
        return 'Channel {} does not appear to be a valid channel file because "{}".'.format(
            self.url, self.reason_message
        )


class InvalidRepoFileException(ProviderException):

    def __init__(self, provider, reason_message):
        self.reason_message = reason_message
        self.url = provider.url

    def __str__(self):
        return "Repository {} does not appear to be a valid repository file because {}".format(
            self.url, self.reason_message
        )


class GitProviderUserInfoException(ProviderException):
    """
    Exception for signalling user information download error.

    The exception is used to indicate a given URL not being in expected form
    to be used by given provider to download user info from.
    """

    def __init__(self, provider):
        self.provider_name = provider.__class__.__name__
        self.url = provider.url

    def __str__(self):
        return '{} unable to fetch user information from "{}".'.format(self.provider_name, self.url)


class GitProviderRepoInfoException(ProviderException):
    """
    Exception for signalling repository information download error.

    The exception is used to indicate a given URL not being in expected form
    to be used by given provider to download repo info from.
    """

    def __init__(self, provider):
        self.provider_name = provider.__class__.__name__
        self.url = provider.url

    def __str__(self):
        return '{} unable to fetch repo information from "{}".'.format(self.provider_name, self.url)


class GitProviderDownloadInfoException(ProviderException):
    """
    Exception for signalling download information download error.

    The exception is used to indicate a given URL not being in expected form
    to be used by given provider to download release information from.
    """

    def __init__(self, provider, url=None):
        self.provider_name = provider.__class__.__name__
        self.url = url or provider.url

    def __str__(self):
        return '{} unable to fetch download information from "{}".'.format(
            self.provider_name, self.url
        )
