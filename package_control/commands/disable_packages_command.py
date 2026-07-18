import sublime
import sublime_aio

from ..package_disabler import PackageDisabler
from ..show_error import show_error


class DisablePackagesCommand(sublime_aio.ApplicationCommand):
    """
    A command that accepts a list of packages to disable,
    or prompts the user to paste a comma-separated list.

    Example:

    ```py
    sublime.run_command("disable_packages", {"packages": ["Package 1", "Package 2"]})
    ```
    """

    async def run(self, packages=None):
        if not packages:
            input_text = await sublime_aio.active_window().show_input_panel(
                "Packages to disable (comma-separated)",
            )
            if input_text:
                packages = []
                for package in input_text.split(","):
                    if package:
                        package = package.strip()
                        if package:
                            packages.append(package)

            if not packages:
                show_error("No package names were entered")
                return

        if not isinstance(packages, list):
            return

        unique_packages = set(packages) - {"Binary", "Default", "Package Control", "Text", "User"}

        disabled = PackageDisabler.disable_packages({PackageDisabler.DISABLE: unique_packages})

        num_packages = len(unique_packages)
        num_disabled = len(disabled)

        if num_packages == num_disabled:
            if num_packages == 1:
                message = "Package {} successfully disabled.".format(packages[0])
            else:
                message = "{} packages have been disabled.".format(num_disabled)
        else:
            message = "{} of {} packages have been disabled.".format(num_disabled, num_packages)

        sublime.status_message(message)
