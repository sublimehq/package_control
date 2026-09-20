import sublime
import sublime_aio

from ..package_disabler import PackageDisabler
from ..package_manager import PackageManager
from ..show_error import show_error


class EnablePackagesCommand(sublime_aio.ApplicationCommand):
    """
    A command that accepts a list of packages to enable,
    or prompts the user to paste a comma-separated list.

    Example:

    ```py
    sublime.run_command("enable_packages", {"packages": ["Package 1", "Package 2"]})
    ```
    """

    async def run(self, packages=None):
        if not packages:
            input_text = await sublime_aio.active_window().show_input_panel(
                "Packages to enable (comma-separated)",
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

        manager = PackageManager()
        unique_packages = set(filter(lambda p: manager.is_compatible(p), packages))

        PackageDisabler.reenable_packages({PackageDisabler.ENABLE: unique_packages})

        if len(unique_packages) == 1:
            message = f"Package {packages[0]} successfully enabled."
        else:
            message = f"{len(unique_packages)} packages have been enabled."

        sublime.status_message(message)
