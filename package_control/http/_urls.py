from __future__ import annotations

import logging
import os
import re
from urllib.parse import unquote_to_bytes, urljoin

__all__ = ("from_uri", "resolve_url", "update_url")

logger = logging.getLogger(__package__)


def from_uri(uri: str) -> str:  # roughly taken from Python 3.13
    """Return a new path from the given 'file' URI."""
    if not uri.lower().startswith("file:"):
        raise ValueError(f"URI does not start with 'file:': {uri!r}")
    path = os.fsdecode(unquote_to_bytes(uri))
    path = path[5:]
    if path[:3] == "///":
        # Remove empty authority
        path = path[2:]
    elif path[:12].lower() == "//localhost/":
        # Remove 'localhost' authority
        path = path[11:]
    if path[:3] == "///" or (path[:1] == "/" and path[2:3] in ":|"):
        # Remove slash before DOS device/UNC path
        path = path[1:]
        path = path[0].upper() + path[1:]
    if path[1:2] == "|":
        # Replace bar with colon in DOS drive
        path = path[:1] + ":" + path[2:]
    if not os.path.isabs(path):
        raise ValueError(f"URI is not absolute: {uri!r}. Parsed so far: {path!r}")
    return path


def resolve_url(root_url: str, url: str) -> str:
    """
    Convert a list of relative uri's to absolute urls/paths.

    :param root_url:
        The root url string

    :param uris:
        An iteratable of relative uri's to resolve.

    :returns:
        A generator of resolved URLs
    """

    if not url:
        return url

    if url.startswith("//"):
        scheme_match = re.match(r"^(file:/|https?:)//", root_url, re.IGNORECASE)
        if scheme_match is not None:
            return scheme_match.group(1) + url
        else:
            return "https:" + url

    elif url.startswith(("./", "../")):
        return urljoin(root_url, url)

    return url


def update_url(url: str) -> str:
    """
    Takes an old, out-dated URL and updates it. Mostly used with GitHub URLs
    since they tend to be constantly evolving their infrastructure.

    :param url:
        The URL to update

    :return:
        The updated URL
    """

    if not url:
        return url

    original_url = url
    url = url.replace("://raw.github.com/", "://raw.githubusercontent.com/")
    url = url.replace("://nodeload.github.com/", "://codeload.github.com/")
    url = re.sub(
        r"^(https://codeload\.github\.com/[^/#?]+/[^/#?]+/)zipball(/.*)$", "\\1zip\\2", url
    )

    # Fix URLs from old versions of Package Control since we are going to
    # remove all packages but Package Control from them to force upgrades
    if (
        url == "https://sublime.wbond.net/repositories.json"
        or url == "https://sublime.wbond.net/channel.json"
    ):
        url = "https://packagecontrol.io/channel_v3.json"

    if url != original_url:
        logger.debug(f"Fixed URL from {original_url} to {url}")

    return url
