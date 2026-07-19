from __future__ import annotations

import asyncio
import concurrent.futures
import io
import os
import sys
import traceback
from abc import ABCMeta
from inspect import iscoroutinefunction
from threading import Event, Lock, Thread
from time import monotonic as now
from typing import TYPE_CHECKING, overload

import sublime
import sublime_api
import sublime_plugin

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from contextvars import Context
    from typing import Callable, List, Tuple, TypeVar, Union

    from typing_extensions import ParamSpec, TypeAlias, TypeVarTuple, Unpack

    P = ParamSpec("P")
    T = TypeVar("T")
    Ts = TypeVarTuple("Ts")

    BlankCoro: TypeAlias = Coroutine[object, None, None]
    CompletionsReturnVal: TypeAlias = Union[
        sublime.CompletionList,
        Tuple[List[sublime.CompletionValue], sublime.AutoCompleteFlags],
        List[sublime.CompletionValue],
        None,
    ]

    EL = TypeVar("EL", bound="EventListener")
    VEL = TypeVar("VEL", bound="ViewEventListener")


__all__ = [
    "__version__",
    "active_window",
    "ApplicationCommand",
    "call_coroutine",
    "call_soon_threadsafe",
    "debounced",
    "EventListener",
    "run_coroutine",
    "TextChangeListener",
    "View",
    "ViewCommand",
    "ViewEventListener",
    "Window",
    "WindowCommand",
    "windows",
]

__version__ = "0.2.7"

# ---- [ internal ] -----------------------------------------------------------

# Make sure to re-use existing loop after library upgrades by (re-)storing
# loop reference in sublime_plugin module, which doesn't change at runtime.
try:
    _loop, _tasks, _thread = sublime_plugin._sublime_aio_globals
except AttributeError:
    _loop = asyncio.new_event_loop()
    _loop.set_default_executor(
        concurrent.futures.ThreadPoolExecutor(thread_name_prefix="sublime_aio.worker")
    )
    asyncio.set_event_loop(_loop)
    _tasks = set()
    _thread = Thread(target=_loop.run_forever, name="sublime_aio", daemon=True)
    _thread.start()
    sublime_plugin._sublime_aio_globals = (_loop, _tasks, _thread)


class ExitEvent:
    """
    A class counting in flight async exit handlers
    """
    _count = 0
    _event = Event()
    _lock = Lock()

    @classmethod
    def aquire(cls):
        with cls._lock:
            cls._count += 1

    @classmethod
    def release(cls):
        with cls._lock:
            cls._count -= 1
            if cls._count == 0:
                cls._event.set()

    @classmethod
    def wait(cls):
        with cls._lock:
            if cls._count == 0:
                return
        cls._event.wait(20.0)


def on_exit(log_path: str):
    """Handle API shutdown uppon application exit

    This custom `on_exit` handler overrides `sublime_plugin.on_exit`
    to ensure to first let plugins handle exit event before closing
    global asyncio event loop.

    Note: Using python's `atexit.register()` does not work as related event
    is not fired and thus eventloop cleanup would not be executed.
    """

    # on_exit() is called once the API it shutdown, which means that stdout
    # will not be visible for debugging. Thus we write to a log file.
    stdout = io.StringIO()
    sys.stdout = stdout
    sys.stderr = stdout

    # execute on_exit event handlers
    for callback in sublime_plugin.el_callbacks('on_exit'):
        callback()

    ExitEvent.wait()

    # shutdown asyncio event loop
    global _loop
    if _loop is not None and _thread is not None:
        loop = _loop
        _loop = None

        def shutdown():
            for task in asyncio.all_tasks(loop):
                task.cancel()
            loop.stop()

        loop.call_soon_threadsafe(shutdown)
        _thread.join()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        asyncio.set_event_loop(None)

    # write stdout to provided logfile
    if len(stdout.getvalue()):
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(stdout.getvalue())
    else:
        os.unlink(log_path)

sublime_plugin.on_exit = on_exit


# ---- [ public ] -------------------------------------------------------------


# Using pyright's type inference to get this type right – for now.
def debounced(delay_in_ms: int):
    """Call coroutine as soon as no more events arrive within specified delay.

    Performs view-specific tracking and is best suited for the
    `on_modified` and `on_selection_modified` methods.
    The `view` is taken from the first argument for `EventListener`s
    and from the instance for `ViewEventListener`s.

    Calls are only made when the `view` is still "valid" according to ST's API,
    so it's not necessary to check it in the wrapped function.

    Examples:

    ```py
    class DebouncedListener(sublime_aio.EventListener):
        @sublime_aio.debounced(500)
        async def on_modified(self, view):
            print("debounced EventListener.on_modified", view.id())

    class DebouncedViewListener(sublime_aio.ViewEventListener):
        @sublime_aio.debounced(1000)
        async def on_modified(self):
            print("debounced ViewEventListener.on_modified_async", self.view.id())
    ```
    """

    @overload
    def decorator(
        coro_func: Callable[[EL, sublime.View], BlankCoro],
    ) -> Callable[[EL, sublime.View], None]: ...

    @overload
    def decorator(coro_func: Callable[[VEL], BlankCoro]) -> Callable[[VEL], None]: ...

    def decorator(
        coro_func: Callable[[EL, sublime.View], BlankCoro] | Callable[[VEL], BlankCoro],
    ) -> Callable[..., None]:
        # Maps a view id to a timestamp of a monotic clock in fractional seconds.
        call_at: dict[int, float] = {}
        lock = Lock()

        async def debounce(
            view: sublime.View, coro_func: Callable, self: EventListener | ViewEventListener, *args
        ):
            """
            Coroutine scheduling delayed event handler coroutine execution.

            Event handler is executed if no further event was received within specified delay.

            :param view:
                The view handling the event for.
            :param coro_func:
                The coroutine function (event listener method) to schedule.
            :param self:
                The event listener instance for which to schedule event handler.
            :param args:
                The arguments passed to coroutine function by ST API.
            """
            while True:
                with lock:
                    time_to_wait = delay_in_ms / 1000 + call_at[view.view_id] - now()
                    if time_to_wait <= 0:
                        del call_at[view.view_id]
                        break

                await asyncio.sleep(time_to_wait)

            if view.is_valid():
                await coro_func(self, *args)

        def wrapper(self: EventListener | ViewEventListener, *args: sublime.View) -> None:
            """
            Wrapper function called on UI thread to schedule debounced coroutine execution

            :param self:
                The event listener instance for which to schedule event handler.
            :param args:
                The arguments passed to coroutine function by ST API.
            """
            if _loop is None:
                return

            view = self.view if isinstance(self, ViewEventListener) else args[0]

            with lock:
                if view.view_id in call_at:
                    call_at[view.view_id] = now()
                    return
                call_at[view.view_id] = now()

            asyncio.run_coroutine_threadsafe(debounce(view, coro_func, self, *args), loop=_loop)

        return wrapper

    return decorator


def run_coroutine(coro: Coroutine[object, object, T]) -> concurrent.futures.Future[T]:
    """
    Run coroutine from synchronous code.

    Example:

    ```py
    import sublime_aio

    async def an_async_func(arg1, arg2):
        ...

    def sync_func(arg1, arg2):

        def on_done(future):
            ...

        future = sublime_aio.run_coroutine(an_async_func(arg1, arg2))
        future.add_done_callback(on_done)
    ```

    :param coro:
        The coroutine object to run

    :returns:
        An `concurrent.futures.Future` object
    """
    if _loop is None:
        raise RuntimeError("No event loop running!")

    return asyncio.run_coroutine_threadsafe(coro, loop=_loop)


def call_coroutine(coro: Coroutine[object, object, object]) -> asyncio.Handle:
    """
    Run coroutine from synchronous code without creating future object.

    A lightweight fire and forget variant to invoke coroutines.

    Example:

    ```py
    import sublime_aio

    async def an_async_func(arg1, arg2):
        ...

    def sync_func(arg1, arg2):
        sublime_aio.call_coroutine(an_async_func(arg1, arg2))
    ```

    :param coro:
        The coroutine object to run

    :returns:
        An `asyncio.ThreadSafeHandle` object
    """
    def callback(coro: Coroutine[object, object, object]) -> None:
        if _loop is None:
            coro.close()
            return

        task = _loop.create_task(coro)
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)

    return call_soon_threadsafe(callback, coro)


def call_soon_threadsafe(
    callback: Callable[[Unpack[Ts]], object],
    *args: Unpack[Ts],
    context: Context | None=None
) -> asyncio.Handle:
    """
    Call specified `callback` function in event loop.

    Example:

    ```py
    import sublime_aio

    def callback(arg1, arg2):
        ...

    def sync_func(arg1, arg2):
        sublime_aio.call_soon_threadsafe(callback, arg1, arg2)
    ```

    :param callback:
        The function to call

    :param args:
        The arguments to pass to the callback function.

    :returns:
        An `asyncio.ThreadSafeHandle` object
    """
    if _loop is None:
        raise RuntimeError("No event loop running!")

    return _loop.call_soon_threadsafe(callback, *args, context=context)


def run_in_worker(func: Callable[[Unpack[Ts]], T], *args: Unpack[Ts]) -> asyncio.Future[T]:
    """
    Call specified `func` function in one of default executors worker threads.

    Example:

    ```py
    import sublime_aio

    def func(arg1, arg2):
        ...

    async def any_coro(arg1, arg2):
        future = await sublime_aio.run_in_worker(func, arg1, arg2)
    ```

    This convenience function is used to execute CPU bound tasks in one of
    default executors worker threads.

    It is equivalent to calling
    `asyncio.get_running_loop().run_in_executor(executor=None, func=func, ...)`

    :param func:
        The function to call

    :param args:
        The arguments to pass to the callback function.

    :returns:
        An `asyncio.Future` object
    """
    if _loop is None:
        raise RuntimeError("No event loop running!")

    return _loop.run_in_executor(None, func, *args)


def active_window() -> Window:
    """
    :returns: The most recently used `Window`.
    """
    return Window(sublime_api.active_window())


def windows() -> list[Window]:
    """
    :returns: A list of all the open windows.
    """
    return [Window(id) for id in sublime_api.windows()]


class ApplicationCommand(sublime_plugin.ApplicationCommand):
    """
    An async `Command` instantiated just once.
    """

    def __init__(self):
        """:meta private:"""
        if not iscoroutinefunction(self.run):
            raise TypeError(f"{type(self).__name__}.run() must be an asyncio coroutine function!")

    def run_(self, edit_token: int, args: sublime.CommandArgs) -> None:
        args = self.filter_args(args)
        try:
            call_coroutine(self.run(**args) if args else self.run())
        except TypeError as e:
            if (
                "required positional argument" in str(e)
                and sublime_api.can_accept_input(self.name(), args)
            ):
                sublime.active_window().run_command(
                    "show_overlay",
                    {"overlay": "command_palette", "command": self.name(), "args": args},
                )
                return
            raise

    async def run(self, **kwargs) -> None:
        """
        Called when the command is run. Command arguments are passed as keyword
        arguments.
        """
        raise NotImplementedError


class WindowCommand(sublime_plugin.WindowCommand):
    """
    An async `Command` instantiated once per window. The `Window` object may be
    retrieved via `self.window <window>`.
    """

    def __init__(self, window: sublime.Window):    # pyright: ignore[reportMissingSuperCall]
        """:meta private:"""
        self.window: Window = Window(window.id())  # pyright: ignore[reportIncompatibleVariableOverride]
        """The asyncio supporting `Window` this command is attached to."""
        if not iscoroutinefunction(self.run):
            raise TypeError(f"{type(self).__name__}.run() must be an asyncio coroutine function!")

    def run_(self, edit_token: int, args: sublime.CommandArgs) -> None:
        args = self.filter_args(args)
        try:
            call_coroutine(self.run(**args) if args else self.run())
        except TypeError as e:
            if (
                "required positional argument" in str(e)
                and sublime_api.window_can_accept_input(self.window.id(), self.name(), args)
            ):
                sublime_api.window_run_command(
                    self.window.id(),
                    "show_overlay",
                    {"overlay": "command_palette", "command": self.name(), "args": args},
                )
                return
            raise

    async def run(self, **kwargs) -> None:
        """
        Called when the command is run. Command arguments are passed as keyword
        arguments.
        """
        raise NotImplementedError


class ViewCommand(sublime_plugin.TextCommand):
    """
    An async `Command` instantiated once per `View`. The `View` object may be
    retrieved via `self.view <view>`.

    It is like a `TextCommand` but doesn't provide an `edit` token, because
    it wouldn't be valid anymore, when `async def run()` is invoked.

    Example:

    ```py
    class MyViewCommand(sublime_aio.ViewCommand):
        async def run(self):
            self.view.close()
    ```
    """

    def __init__(self, view: sublime.View):  # pyright: ignore[reportMissingSuperCall]
        """:meta private:"""
        self.view: View = View(view.id())    # pyright: ignore[reportIncompatibleVariableOverride]
        """The asyncio supporting `View` this command is attached to."""
        if not iscoroutinefunction(self.run):
            raise TypeError(f"{type(self).__name__}.run() must be an asyncio coroutine function!")

    def run_(self, edit_token: int, args: sublime.CommandArgs) -> None:
        args = self.filter_args(args)
        try:
            call_coroutine(self.run(**args) if args else self.run())
        except TypeError as e:
            if (
                "required positional argument" in str(e)
                and sublime_api.window_can_accept_input(self.view.id(), self.name(), args)
            ):
                sublime_api.window_run_command(
                    sublime_api.view_window(self.view.id()),
                    "show_overlay",
                    {"overlay": "command_palette", "command": self.name(), "args": args},
                )
                return
            raise

    async def run(self, **kwargs) -> None:
        """
        Called when the command is run. Command arguments are passed as keyword
        arguments.
        """
        raise NotImplementedError


class CoroutineAdapter:
    """
    This class describes an asyncio coroutine method adapter.

    It wraps a coroutine function to catch exceptions and print tracebacks,
    and enables invokation from synchronous code.
    """
    __slots__ = ("coro_func",)

    @property
    def __name__(self):
        return self.coro_func.__name__

    def __init__(self, coro_func):
        self.coro_func = coro_func

    def __call__(self, *args, **kwargs):
        if _loop is not None:
            _loop.call_soon_threadsafe(self.callback, *args, **kwargs)

    def callback(self, *args, **kwargs):
        if _loop is not None:
            task = _loop.create_task(self.coro_func(*args, **kwargs))
            _tasks.add(task)
            task.add_done_callback(_tasks.discard)


class AsyncEventListenerType(ABCMeta):
    """
    This class describes an asynchronous event listener meta class.

    It wraps all coroutines which start with `on_` into synchronous methods
    for ST to execute them. Wrapper methods schedule execution of coroutines
    in global event loop.

    A `sublime.CompletionList()` is created and returned before async
    `on_query_completions` is scheduled for execution.
    ```
    """

    def __new__(
        mcs: type[AsyncEventListenerType],
        name: str,
        bases: tuple[type, ...],
        attrs: dict[str, object],
    ) -> AsyncEventListenerType:
        for attr_name, attr_value in attrs.items():
            # wrap `async def on_exit()` in sync method of same name
            if attr_name == "on_exit" and iscoroutinefunction(attr_value):
                future = None
                exit_coro: Callable[..., Coroutine[object, object, None]] = attr_value

                def on_exit(*args: P.args, **kwargs: P.kwargs) -> None:
                    nonlocal future
                    ExitEvent.aquire()
                    future = run_coroutine(exit_coro(*args, **kwargs))
                    future.add_done_callback(lambda _: ExitEvent.release())

                attrs[attr_name] = on_exit

            # wrap `async def on_query_completions()` in sync method of same name
            elif attr_name == "on_query_completions" and iscoroutinefunction(attr_value):
                task = None
                completions_coro_func: Callable[
                    ..., Coroutine[object, object, CompletionsReturnVal]
                ] = attr_value

                async def query_completions(
                    clist: sublime.CompletionList,
                    coro: Coroutine[object, object, CompletionsReturnVal],
                ) -> None:
                    nonlocal task
                    if task is not None:
                        task.cancel()
                        task = None

                    try:
                        completions = await (task := asyncio.create_task(coro))
                        if isinstance(completions, sublime.CompletionList):
                            clist.set_completions(completions.completions or [], completions.flags)
                        elif isinstance(completions, tuple):
                            clist.set_completions(completions[0], completions[1])
                        else:
                            clist.set_completions(completions or [])
                    except asyncio.CancelledError:
                        clist.set_completions([])
                    except BaseException:
                        clist.set_completions([])
                        traceback.print_exc()

                def on_query_completions(
                    *args: P.args, **kwargs: P.kwargs
                ) -> sublime.CompletionList:
                    clist = sublime.CompletionList()
                    call_coroutine(query_completions(clist, completions_coro_func(*args, **kwargs)))
                    return clist

                attrs[attr_name] = on_query_completions

            # wrap `async def on_...()` in sync method of same name
            elif attr_name in sublime_plugin.all_callbacks and iscoroutinefunction(attr_value):
                if attr_name.endswith("_async"):
                    raise ValueError(
                        'Invalid event handler name! Coroutines must not end with "_async"!'
                    )
                attrs[attr_name] = CoroutineAdapter(attr_value)

        return super().__new__(mcs, name, bases, attrs)


class EventListener(sublime_plugin.EventListener, metaclass=AsyncEventListenerType):
    """
    This class describes an asyncio event listener.

    It extends `sublime_plugin.EventListener` to support event handler coroutines
    which behave the same way as default methods.

    Example:

    ```py
    class MyEventListener(sublime_aio.EventListener):
        async def on_modified(self, view):
            ...

        async def on_query_completions(self, view):
            # note: CompletionLists must return in resolved state!
            return sublime.CompletionList(["item1", "item2"])
    """

    pass


class ViewEventListener(sublime_plugin.ViewEventListener, metaclass=AsyncEventListenerType):
    """
    This class describes an asyncio view event listener.

    It extends `sublime_plugin.ViewEventListener` to support event handler coroutines
    which behave the same way as default methods.

    Example:

    ```py
    class MyEventListener(sublime_aio.ViewEventListener):
        async def on_modified(self):
            ...

        async def on_query_completions(self):
            # note: CompletionLists must return in resolved state!
            return sublime.CompletionList(["item1", "item2"])
    """

    pass


class AsyncTextChangeListenerType(ABCMeta):
    """
    This class describes an asynchronous text change listener meta class.

    It wraps all coroutines which start with `on_` into synchronous methods
    for ST to execute them. Wrapper methods schedule execution of coroutines
    in global event loop.
    """

    def __new__(
        mcs: type[AsyncTextChangeListenerType],
        name: str,
        bases: tuple[type, ...],
        attrs: dict[str, object],
    ) -> AsyncTextChangeListenerType:
        for attr_name, attr_value in attrs.items():
            # wrap `async def on_...()` in sync method of same name
            if attr_name in sublime_plugin.text_change_listener_callbacks and iscoroutinefunction(
                attr_value
            ):
                if attr_name.endswith("_async"):
                    raise ValueError(
                        'Invalid event handler name! Coroutines must not end with "_async"!'
                    )
                attrs[attr_name] = CoroutineAdapter(attr_value)

        return super().__new__(mcs, name, bases, attrs)


class TextChangeListener(sublime_plugin.TextChangeListener, metaclass=AsyncTextChangeListenerType):
    """
    A class that provides event handling about text changes made to a specific
    Buffer. Is separate from `ViewEventListener` since multiple views can
    share a single buffer.

    It extends `sublime_plugin.TextChangeListener` to support event handler coroutines
    which behave the same way as default methods.

    .. since:: 4081

    .. method:: on_text_changed(changes: List[TextChange])

        Called once after changes has been made to a buffer, with detailed
        information about what has changed.

    .. method:: on_revert()

        Called when the buffer is reverted.

        A revert does not trigger text changes. If the contents of the buffer
        are required here use `View.substr`.

    .. method:: on_reload()

        Called when the buffer is reloaded.

        A reload does not trigger text changes. If the contents of the buffer
        are required here use `View.substr`.
    """

    pass


class Window(sublime.Window):
    """
    This class describes an extended `sublime.Window`.

    It overrides some methods with coroutines.
    """

    def active_view(self) -> View | None:
        """
        :returns: The currently edited `View`.
        """
        view_id = sublime_api.window_active_view(self.window_id)
        if view_id == 0:
            return None
        else:
            return View(view_id)

    def new_file(self, flags=sublime.NewFileFlags.NONE, syntax="") -> View:
        """
        Create a new empty file.

        :param flags: Either ``0``, `NewFileFlags.TRANSIENT` or `NewFileFlags.ADD_TO_SELECTION`.
        :param syntax: The name of the syntax to apply to the file.
        :returns: The view for the file.
        """
        return View(sublime_api.window_new_file(self.window_id, flags, syntax))

    def open_file(self, fname: str, flags=sublime.NewFileFlags.NONE, group=-1) -> View:
        """
        Open the named file. If the file is already opened, it will be brought
        to the front. Note that as file loading is asynchronous, operations on
        the returned view won't be possible until its ``is_loading()`` method
        returns ``False``.

        :param fname: The path to the file to open.
        :param flags: `NewFileFlags`
        :param group: The group to add the sheet to. ``-1`` for the active group.
        """
        return View(sublime_api.window_open_file(self.window_id, fname, flags, group))

    def find_open_file(self, fname: str, group=-1) -> View | None:
        """
        Find a opened file by file name.

        :param fname: The path to the file to open.
        :param group: The group in which to search for the file. ``-1`` for any group.

        :returns: The `View` to the file or ``None`` if the file isn't open.
        """
        view_id = sublime_api.window_find_open_file(self.window_id, fname, group)
        if view_id == 0:
            return None
        else:
            return View(view_id)

    def views(self, *, include_transient: bool=False) -> list[View]:
        """
        :param include_transient: Whether the transient sheet should be included.

            .. since:: 4081
        :returns: All open sheets in the window.
        """
        view_ids = sublime_api.window_views(self.window_id, include_transient)
        return [View(x) for x in view_ids]

    def active_view_in_group(self, group: int) -> View | None:
        """
        :returns: The currently focused `View` in the given group.
        """
        view_id = sublime_api.window_active_view_in_group(self.window_id, group)
        if view_id == 0:
            return None
        else:
            return View(view_id)

    def views_in_group(self, group: int) -> list[View]:
        """
        :returns: A list of all views in the specified group.
        """
        view_ids = sublime_api.window_views_in_group(self.window_id, group)
        return [View(x) for x in view_ids]

    def transient_view_in_group(self, group: int) -> View | None:
        """
        :returns: The transient view in the specified group.
        """
        view_id = sublime_api.window_transient_view_in_group(self.window_id, group)
        if view_id != 0:
            return View(view_id)
        else:
            return None

    def create_output_panel(self, name: str, unlisted: bool=False) -> View:
        """
        Find the `View` associated with the named output panel, creating it if
        required. The output panel can be shown by running the ``show_panel``
        window command, with the ``panel`` argument set to the name with
        an ``"output."`` prefix.

        :param name: The name of the output panel.
        :param unlisted: Control if the output panel should be listed in the panel switcher.
        """
        return View(sublime_api.window_create_output_panel(self.window_id, name, unlisted, None)[0])

    def find_output_panel(self, name: str) -> View | None:
        """
        :returns:
            The `View` associated with the named output panel, or ``None`` if
            the output panel does not exist.
        """
        view_id, _ = sublime_api.window_find_output_panel(self.window_id, name)
        return View(view_id) if view_id else None

    async def show_input_panel(
        self,
        caption: str,
        initial_text: str = "",
        on_change: Callable[[sublime.View, str], Coroutine[object, object, T]] | None = None,
    ) -> str | None:
        view = None
        fut = asyncio.Future()

        def cancel() -> None:
            if _loop:
                _loop.call_soon_threadsafe(fut.set_result, None)

        def done(text: str) -> None:
            if _loop:
                _loop.call_soon_threadsafe(fut.set_result, text)

        def change(text: str) -> None:
            if view is not None:
                call_coroutine(on_change(view, text))

        view = super().show_input_panel(
            caption=caption,
            initial_text=initial_text,
            on_done=done,
            on_change=change if on_change else None,
            on_cancel=cancel,
        )

        return await fut

    async def show_quick_panel(
        self,
        items: list[str] | list[list[str]] | list[sublime.QuickPanelItem],
        flags: sublime.QuickPanelFlags = sublime.QuickPanelFlags.NONE,
        selected_index: int = -1,
        on_highlight: Callable[[int], Coroutine[object, object, T]] | None = None,
        placeholder: str | None = None,
    ) -> int:
        fut = asyncio.Future()

        def highlight(index):
            call_coroutine(on_highlight(index))

        def select(index):
            if _loop:
                _loop.call_soon_threadsafe(fut.set_result, index)

        super().show_quick_panel(
            items=items,
            flags=flags,
            selected_index=selected_index,
            placeholder=placeholder,
            on_highlight=highlight if on_highlight else None,
            on_select=select,
        )

        return await fut


class View(sublime.View):

    def window(self) -> Window | None:
        """
        :returns: A reference to the window containing the view, if any.
        """
        window_id = sublime_api.view_window(self.view_id)
        if window_id == 0:
            return None
        else:
            return Window(window_id)

    def clones(self) -> list[View]:
        """ :returns: All the other views into the same `Buffer`. See `View`. """
        return list(map(View, sublime_api.view_clones(self.view_id)))
