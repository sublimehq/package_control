import sublime
import sublime_aio
import sublime_plugin

from ..activity_indicator import ActivityIndicator
from ..console_write import console_write
from ..package_tasks import PackageTaskRunner
from ..show_error import show_message

STATE_LOADING = 1
STATE_DISPLAY = 2
STATE_CANCELLED = 3


class UpgradePackageCommand(sublime_plugin.ApplicationCommand):
    """
    A command that presents the list of installed packages that can be upgraded

    Note: A synchronous command is used to display a "Loading..." quick panel
    immediatly without any UI flickering, while loading packages in asyncio
    event loop.
    """

    def run(self):
        self.state = STATE_LOADING
        window = sublime.active_window()
        fut = sublime_aio.run_coroutine(self.arun(sublime_aio.Window(window.id())))

        def on_select(picked):
            """
            Cancel execution of arun(), when quick panel is dismissed before
            loading finished.
            """
            if self.state == STATE_LOADING and picked == -1:
                self.state = STATE_CANCELLED
                fut.cancel()

        window.show_quick_panel(items=["Searching updates..."], on_select=on_select)

    async def arun(self, window: sublime_aio.Window):
        upgrader = PackageTaskRunner()

        with ActivityIndicator("Searching updates...") as progress:
            tasks = await upgrader.create_package_tasks(
                actions=(upgrader.PULL, upgrader.UPGRADE),
                ignore_packages=upgrader.ignored_packages(),  # don't upgrade disabled packages
            )
            if tasks is False:
                window.run_command("hide_overlay")
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
                window.run_command("hide_overlay")
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
                details="Use this command to install all available upgrades.",
            ),
        )

        if self.state == STATE_CANCELLED:
            return

        self.state = STATE_DISPLAY
        window.run_command("hide_overlay")

        picked = await window.show_quick_panel(items, sublime.KEEP_OPEN_ON_FOCUS_LOST)
        if picked < 0:
            return

        if picked > 0:
            tasks = [tasks[picked - 1]]

        with ActivityIndicator("Preparing...") as progress:
            await upgrader.run_upgrade_tasks(tasks, progress)
