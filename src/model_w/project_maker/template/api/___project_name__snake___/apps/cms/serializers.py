"""A collection of custom serializers for the CMS app."""

from rest_framework.fields import ReadOnlyField
from wagtail import blocks as wagtail_blocks
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
