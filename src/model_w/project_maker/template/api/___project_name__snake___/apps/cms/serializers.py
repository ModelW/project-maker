"""A collection of custom serializers for the CMS app."""

from rest_framework.fields import ReadOnlyField
from wagtail.rich_text import RichText, expand_db_html


class RichTextSerializer(ReadOnlyField):
    """
    Custom serializer for RichTextField.
    This ensures that embedded elements (eg. images) are included in
    the API response as displayable HTML data, as opposed to just
    their Primary Keys.
    """

    # Annotations are evaluated at runtime by Wagtail's API schema generator,
    # so they must point to real objects
    def to_representation(self, instance: RichText | str) -> str:
        """Expand to full HTML so images can be rendered as is."""
        representation = super().to_representation(instance)
        return expand_db_html(representation)
