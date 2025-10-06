"""
A fixture to compare two images (screenshots) and assert they are the same.

This is used to check if there have been any visual regressions.

Note: The comparison is done using the pixelmatch library, as it's easy to supply
a threshold to ignore small differences, but time will tell if it's OK, or if we
should use another, or roll our own.
Also, the threshold could be adjusted as necessary.

The snapshots are committed to the repo, and so if devs want to update them,
they can use the --update-snapshots flag locally, and commit the changes.
"""

import logging
from collections.abc import Callable
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, ImageChops, ImageFile
from pixelmatch.contrib.PIL import pixelmatch

logger = logging.getLogger(__name__)

SNAPSHOTS_DIRECTORY = Path("bdd") / "__snapshots__"


def get_snapshots_difference(
    image_original: ImageFile,
    image_snapshot: ImageFile,
    threshold: float,
) -> int:
    """Compare two images using a threshold, and return the number of pixels that differ."""
    return pixelmatch(
        image_original,
        image_snapshot,
        threshold=threshold,
    )


@pytest.fixture
def assert_snapshot(
    pytestconfig: pytest.Config,
    request: pytest.FixtureRequest,
) -> Callable[[bytes, str, float], Image.Image | None]:
    """Compare two snapshot images and assert they are the same."""

    def compare(
        image_data: bytes,
        name: str,
        *,
        threshold: float = 1,
    ) -> Image.Image | None:
        """
        Compare two snapshot images and assert they are the same.
        Check if the snapshot exists and if not, warn the user to update snapshots.
        """
        should_update_snapshot = pytestconfig.getoption("--update-snapshots")

        filepath = SNAPSHOTS_DIRECTORY
        filepath.mkdir(parents=True, exist_ok=True)
        file = filepath / name

        output = None

        if should_update_snapshot:
            file.write_bytes(image_data)

        elif not file.exists():
            assert (
                False
            ), "Snapshot not found, use --update-snapshots to update it."

        else:
            old_image = Image.open(file)
            new_image = Image.open(BytesIO(image_data))

            diff = 0
            try:
                diff = get_snapshots_difference(
                    old_image,
                    new_image,
                    threshold=threshold,
                )
            except ValueError as e:
                message = f"Failed to compare snapshots: {e}. Will try and show the difference anyway..."
                logger.exception(message)
                diff = abs(
                    old_image.size[0] * old_image.size[1]
                    - new_image.size[0] * new_image.size[1],
                )

            if diff > 0:
                logger.error("Found a difference of %s pixels for %s", diff, name)
                output = ImageChops.difference(old_image, new_image)

        return output

    return compare
