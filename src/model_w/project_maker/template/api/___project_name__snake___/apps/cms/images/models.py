from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.images.models import AbstractImage, AbstractRendition
from wagtail.images.models import Image as DefaultImage


class CustomImage(AbstractImage):
    """
    Extends the default Wagtail image object to add an "alt" field which is
    often required for SEO purposes.
    """

    alt = models.CharField(
        max_length=1000,
        help_text=_("Default alt text for image."),
        default="",
        blank=True,
    )

    admin_form_fields = (
        *DefaultImage.admin_form_fields,
        "alt",
    )

    class Meta(AbstractImage.Meta):
        verbose_name = _("image")
        verbose_name_plural = _("images")
        permissions = [
            ("choose_image", _("Can choose image")),
        ]


class CustomRendition(AbstractRendition):
    """
    Custom rendition model because we have a custom image model and it's
    mandatory to make the rendition go with it
    """

    image = models.ForeignKey(
        CustomImage,
        related_name="renditions",
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)
