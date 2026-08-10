import os
import re

from .. import __version__


LAST_COMMIT_TIMESTAMP = '2014-11-28 20:54:15'
LAST_COMMIT_VERSION = re.sub(r'[ :\-]', '.', LAST_COMMIT_TIMESTAMP)

GH_USER = os.environ.get('GH_USER', 'packagecontrol-bot')
GH_PASS = os.environ.get('GH_PASS', '')

GL_USER = os.environ.get('GL_USER', '')
GL_PASS = os.environ.get('GL_PASS', '')

BB_USER = os.environ.get('BB_USER', '')
BB_PASS = os.environ.get('BB_PASS', '')

USER_AGENT = 'Package Control %s Unittests' % __version__

DEBUG = False

TEST_REPOSITORY_URL = (
    "https://raw.githubusercontent.com/sublimehq/package_control"
    "/master/package_control/tests/repositories/"
)
"""URL to repository with test data (channels, repositories)"""
