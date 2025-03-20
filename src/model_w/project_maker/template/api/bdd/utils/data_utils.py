"""
Data creation utils to be used in both test fixtures or demo worlds.

For example, users, pages, models, etc.
"""

import httpx
from django.contrib.auth import get_user_model
import logging

# :: IF api__testing
from ___project_name__snake___.apps.cms import models as cms_models
from wagtail import models as wagtail_models
# :: ENDIF

logger = logging.getLogger(__name__)


# :: IF api__wagtail
def get_and_set_up_site(front_server: str) -> wagtail_models.Site:
    """Set up the site."""
    site = wagtail_models.Site.objects.first()
    front_url = httpx.URL(front_server)
    site.port = front_url.port or 80
    site.save()
    return site


def small_image() -> cms_models.CustomImage:
    """Create or get a test image."""
    from wagtail.images.tests.utils import get_image_model, get_test_image_file

    file_name = "___test_image___.png"

    file = get_test_image_file(
        filename=file_name,
        colour="#ffffba",
    )

    image, created = get_image_model().objects.get_or_create(
        title=file_name,
        defaults={"file": file},
    )

    if created:
        logger.debug("Created a new test image model: %s", image)

    return image


# :: ENDIF


def get_or_create_admin_user():
    """
    Create a superuser for ease of debugging.

    Useful to see django / wagtail admin when debugging
    - Will be available in all tests implicitly, so you can
      log in to the admin with the credentials defined here.
    """
    email = "good@user.com"
    password = "correct"  # noqa: S105

    try:
        user = get_user_model().objects.get(email=email)
    except get_user_model().DoesNotExist:
        user = get_user_model().objects.create_superuser(
            email=email,
            password=password,
        )

    return user


# :: IF api__testing
def get_or_create_demo_page(site: wagtail_models.Site) -> cms_models.DemoPage:
    """Create a demo page."""
    slug = "demo"
    home = site.root_page

    demo_page = cms_models.DemoPage.objects.filter(slug=slug).first()

    if not demo_page:
        demo_sub_block = cms_models.DemoSubBlock().to_python(
            {"tagline": "I'm a...", "description": "I'm a DemoSubBlock"},
        )

        demo_block = cms_models.DemoBlock().to_python(
            {
                "tagline": "I'm a...",
                "description": "I'm a DemoBlock",
                "image": small_image().pk,
                "demo_sub_blocks": [("DemoSubBlock", demo_sub_block)],
            },
        )

        demo_page = cms_models.DemoPage(
            title="Demo Page",
            slug=slug,
            tagline="I'm a demo...",
            description="I'm a DemoPage",
            demo_blocks=[("DemoBlock", demo_block)],
        )

        home.add_child(instance=demo_page).save()

    return demo_page


# :: ENDIF


def create_world():
    """
    Create a demo world for ease of development.

    Not a made into a Pytest fixture as it's meant to be used
    more universally, eg. management command/other fixtures/steps.
    """
    get_or_create_admin_user()

    # :: IF api__wagtail
    from django.conf import settings

    site = get_and_set_up_site(settings.BASE_URL)
    # :: ENDIF

    # :: IF api__testing
    get_or_create_demo_page(site)


# :: ENDIF


def remove_world():
    """
    Remove all data created by the create_world function.

    We manually delete as opposed to wiping the DB, as there is
    data created in the migrations that we want to keep, and
    migrating to zero is throwing an error with Wagtail.site Not found.

    Not made into a Pytest fixture as it's meant to be used
    more universally, eg. management command/other fixtures/steps.
    """
    get_user_model().objects.all().delete()
    # :: IF api__testing
    test_data_slugs = ["demo"]
    for slug in test_data_slugs:
        try:
            page = wagtail_models.Page.objects.get(slug=slug)
            page.delete()
        except wagtail_models.Page.DoesNotExist:
            pass


# :: ENDIF
