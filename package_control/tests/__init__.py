# flake8: noqa: F401
try:
    import sublime
except ImportError:
    # Mock the sublime API modules for CLI usage
    from sys import modules
    from . import mock_sublime
    from . import mock_sublime_plugin
    modules["sublime"] = mock_sublime
    modules["sublime_plugin"] = mock_sublime_plugin
else:
    import os

    settings = sublime.load_settings("Package Control.sublime-settings")
    basic_auth = settings.get("http_basic_auth", {})
    if isinstance(basic_auth, dict):
        auth = basic_auth.get("bitbucket.org")
        if isinstance(auth, list) and len(auth) == 2:
            os.environ.setdefault("BB_USER", str(auth[0]))
            os.environ.setdefault("BB_PASS", str(auth[1]))
        auth = basic_auth.get("github.com")
        if isinstance(auth, list) and len(auth) == 2:
            os.environ.setdefault("GH_USER", str(auth[0]))
            os.environ.setdefault("GH_PASS", str(auth[1]))
        auth = basic_auth.get("gitlab.com")
        if isinstance(auth, list) and len(auth) == 2:
            os.environ.setdefault("GL_USER", str(auth[0]))
            os.environ.setdefault("GL_PASS", str(auth[1]))
