"""
Demo snippet, showing how snippets get previewed by the front.

Its front-end counterpart is `front/src/lib/components/cms/snippets/DemoSnippet.svelte`.
Rename it or remove it (along with its migration) once you have your own
snippets.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.api import APIField
from wagtail.fields import RichTextField
from wagtail.models import PreviewableMixin
from wagtail.snippets.models import register_snippet

from . import utils


@register_snippet
class DemoSnippet(utils.ApiSnippet, PreviewableMixin):
    """A snippet with a title and a text, previewed by the front."""

    title = models.CharField(_("title"), max_length=255)
    description = RichTextField(_("description"), blank=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
    ]

    api_fields = [
        APIField("title"),
        APIField("description"),
    ]

    class Meta:
        """Model metadata."""

        verbose_name = _("demo snippet")
        verbose_name_plural = _("demo snippets")

    def __str__(self) -> str:
        """Return the title, for the admin listings."""
        return self.title
