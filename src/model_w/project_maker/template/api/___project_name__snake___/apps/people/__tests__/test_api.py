"""
Test the people app's API functionality.
Unit and integration tests.
"""

from http import HTTPStatus
from importlib import metadata

import pytest
from django.test import Client
from django.urls import reverse

from ___project_name__snake___.apps.people import models

# Uses the global pytestmark variable to add the people marker to all tests in this file.
# This means these tests can be specifically targetted with `pytest -m people`.
pytestmark = [
    pytest.mark.people,
    pytest.mark.django_db(transaction=True, serialized_rollback=True),
]


def test_me_unauthenticated(client: Client):
    """Verify the 'me' endpoint returns unauthenticated status without login."""
    response = client.get(
        reverse(f"api-{metadata.version('~~~project_name__snake~~~')}:me")
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"is_authenticated": False}


def test_me_authenticated(admin_client: Client, admin_user: models.User):
    """Verify the 'me' endpoint returns correct user data when authenticated."""
    response = admin_client.get(
        reverse(f"api-{metadata.version('~~~project_name__snake~~~')}:me")
    )
    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert data["is_authenticated"] is True
    assert data["email"] == admin_user.email
    assert data["first_name"] == admin_user.first_name
    assert data["last_name"] == admin_user.last_name


def test_login(client: Client, admin_user: models.User):
    """Test successful login with valid user credentials."""
    response = client.post(
        reverse(f"api-{metadata.version('~~~project_name__snake~~~')}:login_user"),
        data={"email": admin_user.email, "password": "password"},
        content_type="application/json",
    )
    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert data["is_authenticated"] is True
    assert "email" in data


def test_login_invalid_password(client: Client, admin_user: models.User):
    """Test login failure with an invalid password."""
    response = client.post(
        reverse(f"api-{metadata.version('~~~project_name__snake~~~')}:login_user"),
        data={"email": admin_user.email, "password": "incorrect"},
        content_type="application/json",
    )
    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert data == {"is_authenticated": False}


def test_logout(admin_client: Client):
    """Test successful logout resets authentication status."""
    response = admin_client.post(
        reverse(f"api-{metadata.version('~~~project_name__snake~~~')}:logout_user"),
    )
    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert data == {"is_authenticated": False}
