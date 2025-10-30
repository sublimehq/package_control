import json
import os
import zipfile
from textwrap import dedent
from threading import Thread

import sublime

from . import library, sys_path
from .clear_directory import delete_directory
from .console_write import console_write
from .package_cleanup import PackageCleanup
from .package_disabler import PackageDisabler
from .package_io import create_empty_file
from .show_error import show_message


LOADER_PACKAGE_NAME = '0_package_control_loader'
LOADER_PACKAGE_PATH = os.path.join(
    sys_path.installed_packages_path(),
    LOADER_PACKAGE_NAME + '.sublime-package'
)


def disable_package_control():
    """
    Disables Package Control

    Disabling is executed with little delay to work around a ST core bug,
    which causes `sublime.load_resource()` to fail when being called directly
    by `plugin_loaded()` hook.
    """

    sublime.set_timeout(
        lambda: PackageDisabler.disable_packages({PackageDisabler.DISABLE: 'Package Control'}),
        10
    )


def bootstrap():
    """
    Bootstrap Package Control

    Bootstrapping is executed with little delay to work around a ST core bug,
    which causes `sublime.load_resource()` to fail when being called directly
    by `plugin_loaded()` hook.
    """

    if not os.path.exists(LOADER_PACKAGE_PATH):
        # Start shortly after Sublime starts so package renames don't cause errors
        # with key bindings, settings, etc. disappearing in the middle of parsing
        sublime.set_timeout(PackageCleanup().start, 2000)
        return

    sublime.set_timeout(_bootstrap, 10)


def _bootstrap():
    PackageDisabler.disable_packages({PackageDisabler.LOADER: LOADER_PACKAGE_NAME})
    # Give ST a second to disable 0_package_control_loader
    sublime.set_timeout(Thread(target=_migrate_dependencies).start, 1000)


def _migrate_dependencies():
    """
    Moves old Package Control 3-style dependencies to the new 4-style
    libraries, which use the Lib folder
    """

    # All old dependencies that are being migrated are treated as for 3.3
    # or the first available one, if "3.3" is disabled or does not exist.

    python_version = sys_path.python_versions()[0]
    lib_path = sys_path.lib_paths()[python_version]

    try:
        with zipfile.ZipFile(LOADER_PACKAGE_PATH, 'r') as z:
            for path in z.namelist():
                if path == 'dependency-metadata.json':
                    continue
                if path == '00-package_control.py':
                    continue

                name = path[3:-3]
                try:
                    dep_path = os.path.join(sys_path.packages_path(), name)
                    json_path = os.path.join(dep_path, 'dependency-metadata.json')

                    try:
                        with open(json_path, 'r', encoding='utf-8') as fobj:
                            metadata = json.load(fobj)
                    except (OSError, ValueError) as e:
                        console_write('Error loading dependency metadata during migration - %s' % e)
                        continue

                    did = library.convert_dependency(
                        dep_path,
                        python_version,
                        name,
                        metadata['version'],
                        metadata['description'],
                        metadata['url']
                    )
                    library.install(did, lib_path)

                    if not delete_directory(dep_path):
                        create_empty_file(os.path.join(dep_path, 'package-control.cleanup'))

                except (Exception) as e:
                    console_write('Error trying to migrate dependency %s - %s' % (name, e))

        os.remove(LOADER_PACKAGE_PATH)

        def _reenable_loader():
            PackageDisabler.reenable_packages({PackageDisabler.LOADER: LOADER_PACKAGE_NAME})
            show_message(
                '''
                Dependencies have just been migrated to python libraries.

                You may need to restart Sublime Text.
                '''
            )

        sublime.set_timeout(_reenable_loader, 500)

    except (OSError) as e:
        console_write('Error trying to migrate dependencies - %s' % e)


def _install_injectors():
    """
    Makes sure the module injectors are in place
    """

    injector_code = R'''
        """
        Public Package Control API
        """
        import sys

        try:
            events = __import__(
                "Package Control.package_control.events",
                fromlist=["Package Control.package_control"],
            )
        except Exception:
            if sys.version_info[:2] > (3, 3):
                raise

            from os.path import dirname, join
            from sublime_plugin import ZipLoader

            __zip_path = join(
                dirname(dirname(dirname(__file__))),
                "Installed Packages",
                "Package Control.sublime-package",
            )
            events = ZipLoader(__zip_path).load_module(
                "Package Control.package_control.events"
            )
            del globals()["__zip_path"]
            del globals()["dirname"]
            del globals()["join"]
            del globals()["ZipLoader"]

        events.__name__ = "package_control.events"
        events.__package__ = "package_control"

        if hasattr(events, "__spec__"):
            events.__spec__.name = events.__name__

        sys.modules[events.__name__] = events
        del globals()["sys"]
    '''

    injector_code = dedent(injector_code).lstrip()
    injector_code = injector_code.encode('utf-8')

    for lib_path in sys_path.lib_paths().values():
        injector_path = os.path.join(lib_path, 'package_control.py')

        try:
            with open(injector_path, 'rb') as fobj:
                if injector_code == fobj.read():
                    continue
        except FileNotFoundError:
            pass

        try:
            with open(injector_path, 'wb') as fobj:
                fobj.write(injector_code)
        except FileExistsError:
            pass
        except OSError as e:
            console_write('Unable to write injector to "%s" - %s' % (injector_path, e))


_install_injectors()
