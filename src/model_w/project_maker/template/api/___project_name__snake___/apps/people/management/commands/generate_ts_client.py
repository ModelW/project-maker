"""Generate the TypeScript client of the Ninja API into the front-end."""

import shutil
from http import HTTPStatus
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.test import Client
from django.urls import reverse
from openapi_generator_cli import run as run_oag

# Where the generated client lives, relative to the repo root
CLIENT_DIR = Path("front") / "src" / "lib" / "api" / "client"


class Command(BaseCommand):
    """
    Generate the TypeScript API client from the OpenAPI schema.

    The schema is fetched in-process through Django's test client (no HTTP
    server needed), then fed to openapi-generator's typescript-fetch
    generator, and the result replaces front/src/lib/api/client/ wholesale.
    Run it whenever a Ninja endpoint or schema changes:

        ./pmanage generate_ts_client

    (or `make ts_client`, which also formats the result) and commit the
    result. The front must only talk to the API through this client.
    """

    help = "Generate the TypeScript client from the OpenAPI schema"

    def get_schema(self) -> bytes:
        """Fetch the OpenAPI JSON in-process via the test client."""
        response = Client().get(reverse("api:openapi-json"))

        if response.status_code != HTTPStatus.OK:
            msg = (
                f"Could not fetch the OpenAPI schema ({response.status_code})."
                " The schema URL is only exposed when DEBUG is on."
            )
            raise CommandError(msg)

        return response.content

    def create_client(self, td: Path) -> None:
        """Run openapi-generator on the schema, writing into the temp dir."""
        run_oag(
            [
                "generate",
                *["-i", str(td / "schema.json")],
                *["-g", "typescript-fetch"],
                *["-o", str(td / "client")],
                "--additional-properties=useSingleRequestParameter=false",
            ]
        )

    def copy_client(self, td: Path) -> Path:
        """Replace the committed client with the freshly generated one."""
        target_dir = Path(settings.BASE_DIR).parent / CLIENT_DIR

        shutil.rmtree(target_dir, ignore_errors=True)
        shutil.copytree(
            td / "client",
            target_dir,
            # Generator's own metadata and docs, irrelevant to the app
            ignore=shutil.ignore_patterns(".openapi-generator*", "docs"),
        )

        return target_dir

    def handle(self, *args, **options) -> None:  # noqa: ARG002
        """Fetch the schema, generate the client, move it into the front."""
        with TemporaryDirectory() as td_str:
            td = Path(td_str)

            (td / "schema.json").write_bytes(self.get_schema())
            self.create_client(td)
            target = self.copy_client(td)

        self.stdout.write(self.style.SUCCESS(f"Client generated in {target}"))
