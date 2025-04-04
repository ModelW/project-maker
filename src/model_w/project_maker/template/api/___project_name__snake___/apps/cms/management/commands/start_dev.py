"""Management command to start developing locally from scratch."""

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandParser

from bdd.utils.data_utils import create_world, remove_world


class Command(BaseCommand):
    """
    Prerequisites:
    - Install the project dependencies.
    - Start your local postgres database / redis server.

    This command will:

    - Migrate the database.
    - Remove the current world.
    - Create the demo world.

    Example:
    ```bash
    python manage.py start_dev
    ```

    This will give you the standard local admin user:
    - username: good@user.com
    - password: correct
    """

    help = "Migrate the database and create the demo world."

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add command line arguments to the parser.

        Args:
            parser: The parser object to add arguments to.
        """
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_true",
            help="Skip the confirmation prompt",
        )

    def handle(self, *args, **options):  # noqa: ANN002, ANN003, ARG002
        """
        Migrates the DB
        Clears the current world,
        Creates a new world (to create the admin user etc).

        If the --noinput flag is passed, the confirmation prompt is skipped
        """
        if options["noinput"] or self._user_confirmation():
            self._migrate_database()
            self._remove_world()
            self._create_world()
        else:
            self.stdout.write("Operation cancelled")

    def _user_confirmation(self) -> bool:
        """Ask the user for confirmation before proceeding."""
        message = "Are you sure you want to start from scratch?  Existing data will be deleted. (y/n): "
        return input(message).lower() == "y"

    def _migrate_database(self) -> None:
        """Run the migrations."""
        self.stdout.write("Running migrations...")
        call_command("migrate")
        self.stdout.write("Migrations complete")

    def _remove_world(self) -> None:
        """Remove the current world."""
        self.stdout.write("Removing the current world...")
        remove_world()
        self.stdout.write("World removed")

    def _create_world(self) -> None:
        """Create a demo world."""
        self.stdout.write("Creating world...")
        create_world()
        self.stdout.write("World created")
