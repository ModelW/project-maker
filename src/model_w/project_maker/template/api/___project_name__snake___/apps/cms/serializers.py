"""A collection of custom serializers for the CMS app."""

from rest_framework import serializers as drf_serializers
from rest_framework.fields import ReadOnlyField
from wagtail import blocks as wagtail_blocks
from wagtail.images import models as wagtail_images_models
from wagtail.rich_text import expand_db_html


class RichTextSerializer(ReadOnlyField):
    """
    Custom serializer for RichTextField.
    This ensures that embedded elements (eg. images) are included in
    the API response as displayable HTML data, as opposed to just
    their Primary Keys.
    """

    def to_representation(self, instance: "wagtail_blocks.RichText"):
        """Expand to full HTML so images can be rendered as is."""
        representation = super().to_representation(instance)
        return expand_db_html(representation)


class ImageSourceSerializer(drf_serializers.Serializer):
    """Serializer for a <source> element inside a <picture> tag."""

    srcset = drf_serializers.ListField(child=drf_serializers.CharField())
    image_type = drf_serializers.CharField()
    media = drf_serializers.CharField(allow_null=True, required=False)
    sizes = drf_serializers.CharField(allow_null=True, required=False)


class ImageSerializer(ReadOnlyField):
    """
    Custom serializer for Images.

    To be used in a <picture> tag with a set of renditions in the front
    for example, front/src/lib/components/cms/images/Image.svelte.

    Note: By default, the renditions use a standard width resizing rule, where the aspect ratio is respected.
          However, an array of filters can be passed to better suit your needs.

          See https://docs.wagtail.org/en/stable/topics/images.html#available-resizing-methods
          for the available resizing rules.

    Keyword Args:
        filters (None|list[str]|list[tuple[str, str, str]]): Optional rendition filters to use.

    Example of default behaviour with no filters (image will scale to screen width & DPR):
        ```python
        # with default behaviour
        APIField(
            "image",
            serializer=serializers.ImageSerializer(),
        )
        ```
    Example using a list of resizing rules (image will scale according to the resize rule, to screen width & DPR):
        ```python
        # with custom rendition filters
        APIField(
            "image",
            serializer=serializers.ImageSerializer(
                filters=[
                    "fill-320x350-c100",
                    "fill-640x350-c100",
                    "fill-768x350-c100",
                    "fill-1024x350-c100",
                    "fill-1366x350-c100",
                    "fill-1600x350-c100",
                    "fill-1920x350-c100",
                ],
            ),
        ),
        ```
        Example using a list of resizing rules, media queries and sizes (image will scale according to the resize rule, to media query & DPR if specified):
        ```python
        # with custom rendition filters and media queries (including DPR hint)
        APIField(
            "image",
            serializer=serializers.ImageSerializer(
                filters=[
                    (["fill-768x150-c100", "fill-768x150-c100"], "(max-width: 767px)", "100vw"),
                    (["fill-512x250-c100", "fill-1024x250-c100"], "(max-width: 1023px)", "50vw"),
                    (["fill-360x350-c100", "fill-640x350-c100"], "(min-width: 1024px)", "25vw"),
                ],
            ),
        ),
        ```
    """

    widths = ["320", "640", "768", "1024", "1366", "1600", "1920"]
    formats = ["webp", "jpeg"]

    def __init__(self, *args: any, **kwargs: any) -> None:
        """Accept renditions as a kwarg and then continue as normal."""
        filters = kwargs.pop(
            "filters",
            None,
        )
        if filters is None:
            filters = [f"width-{width}" for width in self.widths]
        else:
            self.validate_filters(filters)

        self.filters = filters
        self.renditions = None
        super().__init__(*args, **kwargs)

    @staticmethod
    def validate_filters(filters: any) -> None:
        """Validate the filters passed to the serializer."""
        error = None
        expected_tuple = ("resizing_rules", "media", "size")

        if not isinstance(filters, list):
            error = "Filters must be a list."
        if not filters:
            error = "Filters cannot be empty."
        for rendition in filters:
            if not isinstance(rendition, str | tuple):
                error = "Filters must be a list of strings or tuples."
            if isinstance(rendition, tuple) and len(rendition) < len(expected_tuple):
                error = "Filters must be a list of strings or tuples."
        if error:
            raise ValueError(error)

    @staticmethod
    def get_wagtail_specification(resize_rule: str, image_type: str) -> str:
        """Return the wagtail specification for the resize rule and image type."""
        return f"{resize_rule}|format-{image_type}"

    def __get_filters(self) -> list[str]:
        """
        Return the filters for the renditions.

        Renditions can either be passed as:
        - a list of rendition filters (e.g. ["width-320", "width-640"])
        - a list of tuples containing rendition filters, a media query and a size
          (e.g. [(["width-320",], "(max-width: 320px)", "100vw")])
        """
        return [
            self.get_wagtail_specification(_filter, image_format)
            for image_format in self.formats
            for rendition in self.filters
            for _filter in ([rendition] if isinstance(rendition, str) else rendition[0])
        ]

    @staticmethod
    def rendition_to_srcset(
        rendition: wagtail_images_models.AbstractRendition,
    ) -> str:
        """Return the srcset for the image."""
        return f"{rendition.url} {rendition.width}w"

    def filters_have_media_queries(self) -> bool:
        """Return True if the filters include media queries (ie. are tuples)."""
        return isinstance(self.filters[0], tuple)

    def __get_sources_without_media_queries(
        self,
        renditions: list[wagtail_images_models.AbstractRendition],
    ) -> list[dict[str, any]]:
        """
        Return the sources without media queries.
        This assumes no filters were passed in to the serializer or they were strings.
        """
        sources: list[dict[str, any]] = []
        for image_type in self.formats:
            srcset = []
            for image_filter in self.filters:
                rendition = renditions[
                    self.get_wagtail_specification(image_filter, image_type)
                ]
                srcset.append(self.rendition_to_srcset(rendition))
            source = ImageSourceSerializer(
                data={
                    "image_type": image_type,
                    "srcset": srcset,
                },
            )
            source.is_valid(raise_exception=True)
            sources.append(source.validated_data)
        return sources

    def __get_sources_with_media(
        self,
        renditions: list[wagtail_images_models.AbstractRendition],
    ) -> list[dict[str, any]]:
        """
        Return the sources with media queries.
        This assumes filters were passed in to the serializer and they were tuples.

        Example:
            self.formats = ["webp", "jpeg"]
            filters = [
                (["width-320", "width-640"], "(max-width: 320px)", "100vw"),
                (["width-768", "width-1024"], "(max-width: 767px)", "50vw"),
                ]
        will return the following sources:
        [
            {
                "srcset": [
                    "https://example.com/image.webp 320w",
                    "https://example.com/image.webp 640w",
                ],
                "media": "(max-width: 320px)",
                "sizes": "100vw",
            },
            {
                "srcset": [
                    "https://example.com/image.webp 768w",
                    "https://example.com/image.webp 1024w",
                ],
                "media": "(max-width: 767px)",
                "sizes": "50vw",
            },
            {
                "srcset": [
                    "https://example.com/image.jpeg 320w",
                    "https://example.com/image.jpeg 640w",
                ],
                "media": "(min-width: 1024px)",
                "sizes": "25vw",
            },
            {
                "srcset": [
                    "https://example.com/image.jpeg 768w",
                    "https://example.com/image.jpeg 1024w",
                ],
                "media": "(min-width: 1024px)",
                "sizes": "25vw",
            },
        ]
        """
        sources: list[dict[str, any]] = []

        for image_type in self.formats:
            for resizing_rules, media, size in self.filters:
                srcset = []
                for resizing_rule in resizing_rules:
                    rendition = renditions[
                        self.get_wagtail_specification(resizing_rule, image_type)
                    ]
                    srcset.append(self.rendition_to_srcset(rendition))
                source = ImageSourceSerializer(
                    data={
                        "image_type": image_type,
                        "srcset": srcset,
                        "media": media,
                        "sizes": size,
                    },
                )
                source.is_valid(raise_exception=True)
                sources.append(source.validated_data)

        return sources

    def __get_sources(
        self,
        instance: wagtail_images_models.AbstractImage,
    ) -> list[dict[str, any]]:
        """
        Return the sources for the image.
        If `self.filters` don't have media queries, there will be 1 source per image format.
        If `self.filters` include media queries, there will be 1 source per media query and image format.
        """
        filters = self.__get_filters()
        renditions = instance.get_renditions(*filters)  # Grab all in 1 query

        if self.filters_have_media_queries():
            sources = self.__get_sources_with_media(renditions)
        else:
            sources = self.__get_sources_without_media_queries(renditions)

        return sources

    def to_representation(self, instance: wagtail_images_models.AbstractImage):
        """
        Return the serialized data as standard, but with the additional
        sources field, which is used by the front to render a picture
        tag with source set to the renditions.
        """
        data = None
        if instance:
            data = {
                "id": instance.id,
                "title": instance.title,
                "url": instance.file.url,
                "alt": instance.alt or "",
                "width": instance.width,
                "height": instance.height,
                "sources": self.__get_sources(instance),
            }
        return data
