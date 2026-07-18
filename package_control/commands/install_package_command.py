import sublime
import sublime_aio

from ..activity_indicator import ActivityIndicator
from ..console_write import console_write
from ..package_tasks import PackageTaskRunner
from ..show_error import show_message


class InstallPackageCommand(sublime_aio.ApplicationCommand):
    """
    A command that presents the list of available packages and allows the
    user to pick one to install.
    """

    async def run(self):
        installer = PackageTaskRunner()

        with ActivityIndicator("Loading packages...") as progress:
            tasks = await installer.create_package_tasks(
                actions=(installer.INSTALL, installer.OVERWRITE)
            )
            if not tasks:
                message = "There are no packages available for installation"
                console_write(message)
                progress.finish(message)
                show_message(
                    """
                    %s

                    Please see https://packagecontrol.io/docs/troubleshooting for help
                    """,
                    message,
                )
                return

        items = installer.render_quick_panel_items(tasks)

        picked = await sublime_aio.active_window().show_quick_panel(items, sublime.KEEP_OPEN_ON_FOCUS_LOST)
        if picked > -1:
            task = tasks[picked]

            with ActivityIndicator("Installing package {}".format(task.package_name)) as progress:
                await installer.run_install_tasks([task], progress)
