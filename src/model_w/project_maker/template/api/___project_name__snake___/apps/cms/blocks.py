"""A collection of custom blocks for the CMS app."""

from wagtail import blocks as wagtail_blocks
from wagtail.images import blocks as wagtail_image_blocks

from . import serializers


class ImageChooserBlock(wagtail_image_blocks.ImageChooserBlock):
    """
    Custom Image chooser block.
    This allows us to use our custom ImageSerializer.

    Note: Like ImageSerializer, filters can be passed as follows:
        ```python
        # with default behaviour
        image = blocks.ImageChooserBlock()
        # with custom rendition filters
        image = blocks.ImageChooserBlock(
            filters=[
                "fill-768x150-c100",
                "fill-512x250-c100",
                "fill-360x350-c100",
            ],
        # with custom rendition filters and media queries
        image = blocks.ImageChooserBlock(
            filters=[
                (["fill-768x150-c100", "fill-768x150-c100"], "(max-width: 767px)", "100vw"),
                (["fill-512x250-c100", "fill-1024x250-c100"], "(max-width: 1023px)", "50vw"),
                (["fill-360x350-c100", "fill-640x350-c100"], "(min-width: 1024px)", "25vw"),
            ],
        ```
    """

    def __init__(self, *args: any, **kwargs: any) -> None:
        """Accept renditions as a kwarg and then continue as normal."""
        self.filters = kwargs.pop("filters", None)
        super().__init__(*args, **kwargs)

    def get_api_representation(self, value, context=None):
        """Return the API representation of the image chooser block."""
        return serializers.ImageSerializer(filters=self.filters).to_representation(
            value,
        )


class RichTextBlock(wagtail_blocks.RichTextBlock):
    """
    Custom RichTextBlock.
    This allows us to use our custom RichTextSerializer which expands
    the value to HTML so that elements with foreign keys, such as inline
    images can be rendered as is.
    """

    def get_api_representation(self, value, context=None):
        """Return the API representation of the RichText block."""
        serializer = serializers.RichTextSerializer()
        return serializer.to_representation(value.source)
