from django.utils.translation import gettext_lazy as _
from wagtail.documents.models import AbstractDocument

# :: IF api__testing
from .demo import *  # noqa: F403

# :: ENDIF
from .utils import ApiPage

from .images.models import CustomImage, CustomRendition  # noqa: F401


class CustomDocument(AbstractDocument):
    """
    Extends the default document object. Does nothing for now but if one day
    you want to add another field to this model then it's going to be much
    easier. Otherwise just let it here.
    """

    admin_form_fields = ("title", "file", "collection", "tags")

    class Meta(AbstractDocument.Meta):
        permissions = [
            ("choose_document", _("Can choose document")),
        ]


class HomePage(ApiPage):
    """
    Home page, expected to be the root of the website. There is already a
    migration that will replace Wagtail's default root page by this. All you
    need to do is add fields there (if needed!).
    """

    parent_page_types = ["wagtailcore.Page"]
