import asyncio

from ..activity_indicator import ActivityIndicator
from ..package_tasks import PackageTaskRunner
from .existing_packages_command import ExistingPackagesCommand


class RevertPackageCommand(ExistingPackagesCommand):
    """
    A command that presents a list of installed packages, allowing the user to
    select one to revert
    """

    def action(self):
        """
        Build a strng to describe the action taken on selected package.
        """

        return "revert to"

    def no_packages_error(self):
        """
        Return the error message to display if no packages are availablw.
        """

        return "There are no built-in package overrides that can be reverted"

    async def list_packages(self, manager):
        """
        Build a list of packages installed by user.

        :param manager:
            The package manager instance to use.

        :returns:
            A list of package names to add to the quick panel
        """
        pkgs1, pkgs2, pkgs3 = await asyncio.gather(
            manager.list_packages(),
            manager.list_default_packages(),
            manager.predefined_packages(),
        )
        return pkgs1 & pkgs2 - pkgs3

    async def on_done(self, manager, package_name):
        """
        Callback function to perform action on selected package.

        :param manager:
            The package manager instance to use.

        :param package_name:
            A package name to perform action for
        """
        with ActivityIndicator() as progress:
            remover = PackageTaskRunner(manager)
            await remover.remove_packages({package_name}, progress)
