"""A collection of custom serializers for the CMS app."""

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


class ImageSerializer(ReadOnlyField):
    """
    Custom serializer for Images.

    To be used in a <picture> tag with src set of renditions in the front
    for example, front/src/lib/components/cms/images/Image.svelte.

    Note: By default, the renditions use width filters, where the aspect ratio is respected.
          However, an array of filters can be passed to better suit your needs.

          See https://docs.wagtail.org/en/stable/topics/images.html#available-resizing-methods
          for the available resizing methods.

    Keyword Args:
        filters (list[str]): A list of rendition filters to use.

    Example:
        ```python
        # with default behaviour
        APIField(
            "image",
            serializer=serializers.ImageSerializer(),
        ),
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
        # with custom rendition filters and media queries
        APIField(
            "image",
            serializer=serializers.ImageSerializer(
                filters=[
                    ("fill-768x150-c100", "(max-width: 767px)"),
                    ("fill-512x250-c100", "(max-width: 1023px)"),
                    ("fill-360x350-c100", "(min-width: 1024px)"),
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

        self.filters = filters
        self.__validate_renditions()
        super().__init__(*args, **kwargs)

    def __validate_renditions(self) -> None:
        """Validate the renditions passed to the serializer."""
        if not isinstance(self.filters, list):
            raise TypeError("Renditions must be a list.")
        if not self.filters:
            raise ValueError("Renditions cannot be empty.")
        for rendition in self.filters:
            if not isinstance(rendition, (str, tuple)):
                raise TypeError("Renditions must be a list of strings or tuples.")
            if isinstance(rendition, tuple) and len(rendition) != 2:
                raise TypeError("Renditions must be a list of strings or tuples.")

    def __get_filters(self) -> list[str]:
        """
        Return the filters for the renditions.

        Renditions can either be passed as:
        - a list of rendition filters (e.g. ["width-320", "width-640"])
        - a list of rendition filters and media query tuples
          (e.g. [("width-320", "(max-width: 320px)")])
        """
        filters = []
        for rendition_format in self.formats:
            for rendition in self.filters:
                if isinstance(rendition, str):
                    filters.append(f"{rendition}|format-{rendition_format}")
                else:
                    filters.append(f"{rendition[0]}|format-{rendition_format}")
        return filters

    def __get_rendition_media_query(
        self,
        rendition_filter: str | tuple[str, str],
        rendition: list[wagtail_images_models.AbstractRendition],
    ) -> list[str]:
        """Return the media query for the rendition."""
        if isinstance(rendition_filter, str):
            return [f"(max-width: {rendition.width - 1}px)"]
        return [rendition_filter[1]]

    def to_representation(self, instance: wagtail_images_models.AbstractImage):
        """
        Return the serialized data as standard, but with the additional
        renditions field, which is used by the front to render a picture
        tag with source set to the renditions.
        """
        filters = self.__get_filters()

        renditions = instance.get_renditions(
            *filters,
        )

        return {
            "id": instance.id,
            "title": instance.title,
            "url": instance.file.url,
            "alt": instance.alt or "",
            "width": instance.width,
            "height": instance.height,
            "renditions": [
                {
                    "name": name,
                    "url": rendition.url,
                    "width": rendition.width,
                    "height": rendition.height,
                    "media_query": self.__get_rendition_media_query(
                        self.filters[i // len(self.formats)],
                        rendition,
                    ),
                }
                for i, (name, rendition) in enumerate(renditions.items())
            ],
        }
