import sublime_aio

from ..activity_indicator import ActivityIndicator
from ..console_write import console_write
from ..package_tasks import PackageTaskRunner
from ..show_error import show_error


class InstallPackagesCommand(sublime_aio.ApplicationCommand):
    """
    A command that accepts a list of packages to install,
    or prompts the user to paste a comma-separated list.

    Example:

    ```py
    sublime.run_command(
        "install_packages",
        {
            "packages": ["Package 1", "Package 2"],
            "unattended": False  # if True, suppress error dialogs
        }
    )
    ```
    """

    async def run(self, packages=None, unattended=False):
        if not packages:
            input_text = await sublime_aio.active_window().show_input_panel(
                "Packages to install (comma-separated)",
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

        message = "Loading packages..."
        with ActivityIndicator(message) as progress:
            installer = PackageTaskRunner()
            console_write(message)
            await installer.install_packages(packages, unattended, progress)
