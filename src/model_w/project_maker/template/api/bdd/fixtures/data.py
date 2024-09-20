"""
Fixtures related to any global data needed when testing

For example, users, pages, models, etc.
"""

from urllib.parse import urlparse

import pytest
from django.contrib.auth.models import AbstractBaseUser
from pytest_django.fixtures import SettingsWrapper

# :: IF api__wagtail
from wagtail.images.tests.utils import Image, get_test_image_file

# :: ENDIF


# :: IF api__wagtail
@pytest.fixture
def image():
    """Create an test image."""
    image_file = get_test_image_file(filename="test.png")
    return Image.objects.create(title="Test Image", file=image_file)


@pytest.fixture(autouse=True)
def set_wagtail_site(front_server: str, overwrite_settings: SettingsWrapper):
    """
    Set the wagtail site as needed.

    Port should be the same as the front server.
    """
    from wagtail.models import Site

    url = urlparse(front_server)

    site = Site.objects.get(is_default_site=True)
    site.hostname = url.hostname
    site.port = url.port
    site.save()


# :: ENDIF


@pytest.fixture(autouse=True)
def admin_user(django_user_model: AbstractBaseUser):
    """
    Create a superuser for ease of debugging.

    Useful to see django / wagtail admin when debugging
    - Will be available in all tests implicitly, so you can
      log in to the admin with the credentials defined here.
    """
    email = "good@user.com"
    password = "correct"

    try:
        user = django_user_model.objects.get(email=email)
    except django_user_model.DoesNotExist:
        user = django_user_model.objects.create_superuser(
            email=email,
            password=password,
        )

    return user
