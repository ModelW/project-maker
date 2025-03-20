"""
Fixtures related to any global data needed when testing

For example, users, pages, models, etc.
"""

import pytest
from pytest_django.fixtures import SettingsWrapper

from bdd.utils import data_utils


# :: IF api__wagtail
from wagtail.images.tests.utils import Image, get_test_image_file

# :: ENDIF

# :: IF api__testing
from ___project_name__snake___.apps.cms import models as cms_models
from wagtail import models as wagtail_models
# :: ENDIF


# :: IF api__wagtail
@pytest.fixture
def image():
    """Create an test image."""
    image_file = get_test_image_file(filename="test.png")
    return Image.objects.create(title="Test Image", file=image_file)


@pytest.fixture(autouse=True)
def site(front_server: str, overwrite_settings: SettingsWrapper):
    """Fixture to make sure the site is set up."""
    return data_utils.get_and_set_up_site(front_server)


# :: ENDIF


@pytest.fixture(autouse=True)
def admin_user():
    """Fixture to make sure the admin user is set up."""
    return data_utils.get_or_create_admin_user()


# :: IF api__testing
@pytest.fixture
def demo_page(site: wagtail_models.Site) -> cms_models.DemoPage:
    """Fixture to create a demo page."""
    return data_utils.get_or_create_demo_page(site)


# :: ENDIF
