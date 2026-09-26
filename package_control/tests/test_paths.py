import sys
import unittest

from ..sys_path import longpath, shortpath
from ._data_decorator import data, data_decorator


@data_decorator
@unittest.skipIf(sys.platform == "win32", "Relevant only on MacOS/Linux")
class UnixPathTests(unittest.TestCase):
    @data(
        (
            # convert short -> long
            (R"folder", R"folder"),
            (R"C:\folder", R"C:\folder"),
            (R"C:/folder", R"C:/folder"),
            (R"/folder", R"/folder"),
            (R"\\localhost\folder", R"\\localhost\folder"),
            (R"\\localhost/folder", R"\\localhost/folder"),
        )
    )
    def longpath(self, input, result):
        self.assertEqual(longpath(input), result)

    @data(
        (
            # convert long -> short
            (R"folder", R"folder"),
            (R"C:\folder", R"C:\folder"),
            (R"C:/folder", R"C:/folder"),
            (R"/folder", R"/folder"),
            (R"\\localhost\folder", R"\\localhost\folder"),
        )
    )
    def shortpath(self, input, result):
        self.assertEqual(shortpath(input), result)


@data_decorator
@unittest.skipIf(sys.platform != "win32", "Relevant only on Windows")
class WindowsPathTests(unittest.TestCase):
    @data(
        (
            # convert short -> long
            (R"folder", R"\\?\folder"),
            (R"C:\folder", R"\\?\C:\folder"),
            (R"C:/folder", R"\\?\C:\folder"),
            (R"\\localhost\folder", R"\\?\UNC\localhost\folder"),
            (R"\\localhost/folder", R"\\?\UNC\localhost\folder"),
            # long paths unchanged
            (R"\\?\C:\folder", R"\\?\C:\folder"),
            (R"\\?\UNC\localhost\folder", R"\\?\UNC\localhost\folder"),
        )
    )
    def longpath(self, input, result):
        self.assertEqual(longpath(input), result)

    @data(
        (
            # convert long -> short
            (R"\\?\folder", R"folder"),
            (R"\\?\C:\folder", R"C:\folder"),
            (R"\\?\UNC\localhost\folder", R"\\localhost\folder"),
            # short paths unchanged
            (R"C:\folder", R"C:\folder"),
            (R"\\localhost\folder", R"\\localhost\folder"),
        )
    )
    def shortpath(self, input, result):
        self.assertEqual(shortpath(input), result)
