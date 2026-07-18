import sublime
import sublime_aio

from ..activity_indicator import ActivityIndicator
from ..console_write import console_write
from ..package_tasks import PackageTaskRunner
from ..show_error import show_message


class UpgradePackageCommand(sublime_aio.ApplicationCommand):
    """
    A command that presents the list of installed packages that can be upgraded
    """

    async def run(self):
        upgrader = PackageTaskRunner()

        with ActivityIndicator("Searching updates...") as progress:
            tasks = await upgrader.create_package_tasks(
                actions=(upgrader.PULL, upgrader.UPGRADE),
                ignore_packages=upgrader.ignored_packages(),  # don't upgrade disabled packages
            )
            if tasks is False:
                message = "There are no packages available for upgrade"
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

            if not tasks:
                message = "All packages up-to-date!"
                console_write(message)
                progress.finish(message)
                show_message(message)
                return

        items = upgrader.render_quick_panel_items(tasks)
        items.insert(
            0,
            sublime.QuickPanelItem(
                trigger="Upgrade All Packages",
                details="Use this command to install all available upgrades."
            ),
        )

        picked = await sublime_aio.active_window().show_quick_panel(items, sublime.KEEP_OPEN_ON_FOCUS_LOST)
        if picked < 0:
            return

        if picked > 0:
            tasks = [tasks[picked - 1]]

        with ActivityIndicator("Preparing...") as progress:
            await upgrader.run_upgrade_tasks(tasks, progress)
