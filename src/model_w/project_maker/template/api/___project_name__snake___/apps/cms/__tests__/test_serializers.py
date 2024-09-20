"""Test the serializers for the CMS app."""

import pytest
from wagtail.images.models import AbstractImage
from wagtail.images.tests.utils import Image, get_test_image_file

from ___project_name__snake___.apps.cms import serializers
from bdd.fixtures.front import *  # noqa: F403

# Uses the global pytestmark variable to add the cms_serializers marker to all tests in this file.
# This means these tests can be specifically targetted with `pytest -m cms_serializers`.
pytestmark = [
    pytest.mark.django_db(transaction=True, serialized_rollback=True),
    pytest.mark.cms_serializers,
]


@pytest.fixture
def large_image():
    """Create a large test image."""
    image_file = get_test_image_file(filename="test.png", size=(2000, 2000))
    return Image.objects.create(title="Test Image", file=image_file)


@pytest.fixture
def small_image():
    """Create a small test image."""
    image_file = get_test_image_file(filename="test.png", size=(200, 200))
    return Image.objects.create(title="Test Image", file=image_file)


def test_image_source_serializer_valid_data_all():
    """Test ImageSourceSerializer with all valid data."""
    data = {
        "srcset": ["image1.webp 320w", "image2.webp 640w"],
        "image_type": "webp",
        "media": "(max-width: 1024px)",
        "sizes": "100vw",
    }
    serializer = serializers.ImageSourceSerializer(data=data)
    assert serializer.is_valid()


def test_image_source_serializer_valid_data_required():
    """Test ImageSourceSerializer with valid required data."""
    data = {
        "srcset": ["image1.webp 320w", "image2.webp 640w"],
        "image_type": "webp",
    }
    serializer = serializers.ImageSourceSerializer(data=data)
    assert serializer.is_valid()


def test_image_serializer_valid_default(large_image: AbstractImage):
    """
    Test ImageSerializer with no arguments.

    Expected response is:
    {
        "id": 1,
        "title": "Test Image",
        "url": "{baseurl}/original_images/test_2ultByX.png",
        "alt": "",
        "width": 2000,
        "height": 2000,
        "sources": [
            {
                "srcset": [
                    "{baseurl}/images/test_2ultByX.width-320.format-webp.webp 320w",
                    "{baseurl}/images/test_2ultByX.width-640.format-webp.webp 640w",
                    "{baseurl}/images/test_2ultByX.width-768.format-webp.webp 768w",
                    "{baseurl}/images/test_2ultByX.width-1024.format-webp.webp 1024w",
                    "{baseurl}/images/test_2ultByX.width-1366.format-webp.webp 1366w",
                    "{baseurl}/images/test_2ultByX.width-1600.format-webp.webp 1600w",
                    "{baseurl}/images/test_2ultByX.width-1920.format-webp.webp 1920w",
                ],
                "image_type": "webp",
            },
            {
                "srcset": [
                    "{baseurl}/images/test_2ultByX.width-320.format-jpeg.jpg 320w",
                    "{baseurl}/images/test_2ultByX.width-640.format-jpeg.jpg 640w",
                    "{baseurl}/images/test_2ultByX.width-768.format-jpeg.jpg 768w",
                    "{baseurl}/images/test_2ultByX.width-1024.format-jpeg.jpg 1024w",
                    "{baseurl}/images/test_2ultByX.width-1366.format-jpeg.jpg 1366w",
                    "{baseurl}/images/test_2ultByX.width-1600.format-jpeg.jpg 1600w",
                    "{baseurl}/images/test_2ultByX.width-1920.format-jpeg.jpg 1920w",
                ],
                "image_type": "jpeg",
            },
        ],
    }
    """
    image_serializer = serializers.ImageSerializer()
    data = image_serializer.to_representation(large_image)

    assert data["id"] == large_image.id
    assert data["title"] == large_image.title
    assert data["url"] == large_image.file.url
    assert data["alt"] == ""
    assert data["width"] == large_image.width
    assert data["height"] == large_image.height

    for source_index, source in enumerate(data["sources"]):
        image_format = image_serializer.formats[source_index]
        assert source["image_type"] == image_format
        for srcset_index, src in enumerate(source["srcset"]):
            url, width = src.split(" ")
            assert width == f"{image_serializer.widths[srcset_index]}w"
            if image_format == "jpeg":
                assert url.endswith(".jpg")
            else:
                assert url.endswith(
                    f".{image_format}",
                )


def test_image_serializer_valid_default_with_small_image(small_image: AbstractImage):
    """
    Test ImageSerializer with no arguments but with an image smaller than all filters.
    By default, the renditions are still created for each filter, but all at the smaller size.
    This could potentially be improved by bailing out before creating essentially duplicate renditions,
    but as it's an edge case, and the front still only uses the first rendition, this is not implemented yet.

    Expected response is:
    {
        "id": 1,
        "title": "Test Image",
        "url": "{baseurl}/original_images/test_2ultByX.png",
        "alt": "",
        "width": 200,
        "height": 200,
        "sources": [
            {
                "srcset": [
                    "{baseurl}/images/test_2ultByX.width-320.format-webp.webp 200w",
                    "{baseurl}/images/test_2ultByX.width-640.format-webp.webp 200w",
                    "{baseurl}/images/test_2ultByX.width-768.format-webp.webp 200w",
                    "{baseurl}/images/test_2ultByX.width-1024.format-webp.webp 200w",
                    "{baseurl}/images/test_2ultByX.width-1366.format-webp.webp 200w",
                    "{baseurl}/images/test_2ultByX.width-1600.format-webp.webp 200w",
                    "{baseurl}/images/test_2ultByX.width-1920.format-webp.webp 200w",
                ],
                "image_type": "webp",
            },
            {
                "srcset": [
                    "{baseurl}/images/test_2ultByX.width-320.format-jpeg.jpg 200w",
                    "{baseurl}/images/test_2ultByX.width-640.format-jpeg.jpg 200w",
                    "{baseurl}/images/test_2ultByX.width-768.format-jpeg.jpg 200w",
                    "{baseurl}/images/test_2ultByX.width-1024.format-jpeg.jpg 200w",
                    "{baseurl}/images/test_2ultByX.width-1366.format-jpeg.jpg 200w",
                    "{baseurl}/images/test_2ultByX.width-1600.format-jpeg.jpg 200w",
                    "{baseurl}/images/test_2ultByX.width-1920.format-jpeg.jpg 200w",
                ],
                "image_type": "jpeg",
            },
        ],
    }
    """
    image_serializer = serializers.ImageSerializer()
    data = image_serializer.to_representation(small_image)

    assert data["id"] == small_image.id
    assert data["title"] == small_image.title
    assert data["url"] == small_image.file.url
    assert data["alt"] == ""
    assert data["width"] == small_image.width
    assert data["height"] == small_image.height

    for source_index, source in enumerate(data["sources"]):
        image_format = image_serializer.formats[source_index]
        assert source["image_type"] == image_format
        for src in source["srcset"]:
            url, width = src.split(" ")
            assert width == f"{small_image.width}w"
            if image_format == "jpeg":
                assert url.endswith(".jpg")
            else:
                assert url.endswith(
                    f".{image_format}",
                )


def test_image_serializer_valid_with_custom_filters(large_image: AbstractImage):
    """
    Test ImageSerializer with custom filters (strings).

    Expected response is:
    {
        "id": 1,
        "title": "Test Image",
        "url": "{baseurl}/original_images/test_2ultByX.png",
        "alt": "",
        "width": 2000,
        "height": 2000,
        "sources": [
            {
                "srcset": [
                    "{baseurl}/images/test_2ultByX.fill-320x350-c100.format-webp.webp 320w",
                ],
                "image_type": "webp",
            },
            {
                "srcset": [
                    "{baseurl}/images/test_2ultByX.fill-320x350-c100.format-jpeg.jpg 320w",
                ],
                "image_type": "jpeg",
            },
        ],
    }
    """
    widths = ["320"]
    filters = [f"fill-{width}x350-c100" for width in widths]

    image_serializer = serializers.ImageSerializer(
        filters=filters,
    )
    data = image_serializer.to_representation(large_image)

    assert data["id"] == large_image.id
    assert data["title"] == large_image.title
    assert data["url"] == large_image.file.url
    assert data["alt"] == ""
    assert data["width"] == large_image.width
    assert data["height"] == large_image.height

    for source_index, source in enumerate(data["sources"]):
        image_format = image_serializer.formats[source_index]
        assert source["image_type"] == image_format
        for srcset_index, src in enumerate(source["srcset"]):
            url, width = src.split(" ")
            assert width == f"{widths[srcset_index]}w"
            if image_format == "jpeg":
                assert url.endswith(".jpg")
            else:
                assert url.endswith(
                    f".{image_format}",
                )


def test_image_serializer_valid_with_custom_filters_and_media_queries(
    large_image: AbstractImage,
):
    """
    Test ImageSerializer with custom filters and media queries (tuples).

    Expected response is:
    {
        "id": 1,
        "title": "Test Image",
        "url": "{baseurl}/original_images/test_2ultByX.png",
        "alt": "",
        "width": 2000,
        "height": 2000,
        "sources": [
            {
                "srcset": [
                    "{baseurl}/images/test_2ultByX.fill-320x150-c100.format-webp.webp 320w",
                    "{baseurl}/images/test_2ultByX.fill-640x150-c100.format-webp.webp 640w",
                ],
                "image_type": "webp",
                "media": "(max-width: 767px)",
                "sizes": "100vw",
            },
            {
                "srcset": [
                    "{baseurl}/images/test_2ultByX.fill-768x350-c100.format-webp.webp 320w",
                    "{baseurl}/images/test_2ultByX.fill-1536x350-c100.format-webp.webp 640w",
                ],
                "image_type": "webp",
                "media": "(min-width: 768px)",
                "sizes": "25vw",
            },
            {
                "srcset": [
                    "{baseurl}/images/test_2ultByX.fill-320x150-c100.format-jpeg.jpg 320w",
                    "{baseurl}/images/test_2ultByX.fill-640x150-c100.format-jpeg.jpg 640w",
                ],
                "image_type": "jpeg",
                "media": "(max-width: 767px)",
                "sizes": "100vw",
            },
                        {
                "srcset": [
                    "{baseurl}/images/test_2ultByX.fill-768x350-c100.format-jpeg.jpg 320w",
                    "{baseurl}/images/test_2ultByX.fill-1536x350-c100.format-jpeg.jpg 640w",
                ],
                "image_type": "webp",
                "media": "(min-width: 768px)",
                "sizes": "25vw",
            },
        ],
    }
    """
    widths = [320, 768]
    filters = [
        (
            [f"fill-{widths[0]}x150-c100", f"fill-{widths[0] * 2}x250-c100"],
            f"(max-width: {widths[0] - 1}px)",
            "100vw",
        ),
        (
            [f"fill-{widths[1]}x350-c100", f"fill-{widths[1] * 2}x350-c100"],
            f"(min-width: {widths[1]}px)",
            "25vw",
        ),
    ]

    expected_source_widths = {
        0: [widths[0], widths[0] * 2],
        1: [widths[1], widths[1] * 2],
    }

    image_serializer = serializers.ImageSerializer(
        filters=filters,
    )
    data = image_serializer.to_representation(large_image)

    assert data["id"] == large_image.id
    assert data["title"] == large_image.title
    assert data["url"] == large_image.file.url
    assert data["alt"] == ""
    assert data["width"] == large_image.width
    assert data["height"] == large_image.height
    for source_index, source in enumerate(data["sources"]):
        image_format = image_serializer.formats[source_index // len(filters)]
        assert source["image_type"] == image_format
        for srcset_index, src in enumerate(source["srcset"]):
            url, width = src.split(" ")
            assert (
                width
                == f"{expected_source_widths[source_index % len(expected_source_widths)][srcset_index]}w"
            )
            if image_format == "jpeg":
                assert url.endswith(".jpg")
            else:
                assert url.endswith(
                    f".{image_format}",
                )
