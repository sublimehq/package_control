import sublime_aio

from ..activity_indicator import ActivityIndicator
from ..package_tasks import PackageTaskRunner
from ..show_error import show_error


class RemovePackagesCommand(sublime_aio.ApplicationCommand):
    """
    A command that accepts a list of packages to remove,
    or prompts the user to paste a comma-separated list.

    Example:

    ```py
    sublime.run_command("remove_packages", {"packages": ["Package 1", "Package 2"]})
    ```
    """

    async def run(self, packages=None):
        if not packages:
            input_text = await sublime_aio.active_window().show_input_panel(
                "Packages to remove (comma-separated)",
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

        with ActivityIndicator() as progress:
            remover = PackageTaskRunner()
            await remover.remove_packages(packages, progress)
