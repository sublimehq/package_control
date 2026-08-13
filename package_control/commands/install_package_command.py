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


class InstallPackageCommand(sublime_plugin.ApplicationCommand):
    """
    A command that presents the list of available packages and allows the
    user to pick one to install.

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

        window.show_quick_panel(items=["Loading packages..."], on_select=on_select)

    async def arun(self, window: sublime_aio.Window):
        installer = PackageTaskRunner()

        with ActivityIndicator("Loading packages...") as progress:
            tasks = await installer.create_package_tasks(
                actions=(installer.INSTALL, installer.OVERWRITE)
            )
            if not tasks:
                window.run_command("hide_overlay")
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

        if self.state == STATE_CANCELLED:
            return

        self.state = STATE_DISPLAY
        window.run_command("hide_overlay")

        picked = await window.show_quick_panel(items, sublime.KEEP_OPEN_ON_FOCUS_LOST)
        if picked < 0:
            return

        task = tasks[picked]

        with ActivityIndicator("Installing package {}".format(task.package_name)) as progress:
            await installer.run_install_tasks([task], progress)
