"""
Used only for demo purposes inside the project maker template.

It is not to be included in the project itself.

To make removal easier, it's one big melting pot of different functionality.
"""

from django.db import models
from django.utils.translation import gettext as _
from wagtail import blocks as wagtail_blocks
from wagtail import fields as wagtail_fields
from wagtail.admin import panels
from wagtail.api import APIField
from wagtail.blocks import StreamValue
from wagtail.images import get_image_model
from wagtail.rich_text import RichText

from . import blocks, serializers, utils
from .images import serializers as image_serializers


class DemoSubBlock(wagtail_blocks.StructBlock):
    """
    Demo sub block that is used to show how to test a wide selection of
    functionality that a CMS block can have.
    """

    tagline = wagtail_blocks.CharBlock(
        required=True,
        max_length=255,
        help_text=_("This is a required tagline"),
    )
    description = blocks.RichTextBlock(
        required=False,
        help_text=_("This is an optional description"),
    )

    image = blocks.ImageChooserBlock(
        required=False,
        help_text=_("This is an optional image"),
        filters=[
            (
                ["fill-768x150-c100", "fill-1024x250-c100"],
                "(max-width: 767px)",
                "100vw",
            ),
            (
                ["fill-512x250-c100", "fill-1024x250-c100"],
                "(max-width: 1023px)",
                "50vw",
            ),
            (
                ["fill-360x350-c100", "fill-640x350-c100"],
                "(min-width: 1024px)",
                "25vw",
            ),
        ],
    )

    heading_blocks = wagtail_blocks.StreamBlock(
        [
            (
                "Heading",
                wagtail_blocks.CharBlock(),
            ),
        ],
        required=False,
    )


class DemoBlock(wagtail_blocks.StructBlock):
    """
    Demo block that is used to show how to test a wide selection of
    functionality that a CMS block can have.
    """

    tagline = wagtail_blocks.CharBlock(
        required=True,
        max_length=255,
        help_text=_("This is a required tagline"),
    )
    description = blocks.RichTextBlock(
        required=False,
        help_text=_("This is an optional description"),
    )

    demo_sub_blocks = wagtail_blocks.StreamBlock(
        [
            (
                "DemoSubBlock",
                DemoSubBlock(),
            ),
        ],
        required=False,
    )

    image = blocks.ImageChooserBlock(
        required=False,
        help_text=_("This is an optional image"),
    )

    class Meta:
        preview_template = True
        description = "A demo block containing a rich text field, a demo sub block, and a demo image."

    def get_preview_value(self):
        """Show a preview value for the block in the CMS admin, with access to the DB."""
        return {
            "tagline": "I'm the demo block preview value tagline.",
            "description": RichText(
                "<h3>I'm a preview value description.</h3><ol><li>I'm a preview value list item.</li></ol>",
            ),
            "image": get_image_model().objects.first(),
            "demo_sub_blocks": StreamValue(
                self.child_blocks["demo_sub_blocks"],
                [
                    (
                        "DemoSubBlock",
                        DemoSubBlock().to_python(
                            {
                                "tagline": "I'm a preview value demo sub block tagline.",
                            },
                        ),
                    ),
                ],
            ),
        }


class DemoPage(utils.ApiPage):
    """
    Demo page that is used to show how to test a wide selection of
    functionality that a CMS page can have.

    Note: The template field is required for the front to know where to retrieve
    the page component, and should be prefixed with $lib and end with .svelte.
    """

    tagline = models.CharField(
        max_length=255,
        help_text=_("This is a required tagline"),
    )
    description = wagtail_fields.RichTextField(
        blank=True,
        help_text=_("This is an optional description"),
    )

    demo_blocks = wagtail_fields.StreamField(
        [
            ("DemoBlock", DemoBlock()),
            ("DemoSubBlock", DemoSubBlock()),
        ],
        blank=True,
    )

    image = models.ForeignKey(
        "cms.CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    api_fields = [
        APIField("tagline"),
        APIField("description", serializer=serializers.RichTextSerializer()),
        APIField("demo_blocks"),
        APIField(
            "image",
            serializer=image_serializers.ImageSerializer(
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
    ]

    content_panels = [
        *utils.ApiPage.content_panels,
        panels.FieldPanel("tagline"),
        panels.FieldPanel("description"),
        panels.FieldPanel("demo_blocks"),
        panels.FieldPanel("image"),
    ]

    class Meta:
        verbose_name = _("Demo Page")
        verbose_name_plural = _("Demo Pages")
