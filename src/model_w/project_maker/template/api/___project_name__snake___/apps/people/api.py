"""API endpoints for the people app."""

import logging

from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest
from ninja import Router
from ninja.security import django_auth

from . import schemas
from .schemas import AnonUserOut, AuthUserIn

logger = logging.getLogger(__name__)

router = Router(auth=django_auth, tags=["me"])


@router.get("/", auth=None, response=schemas.AuthUserOut | schemas.AnonUserOut)
def me(request: HttpRequest):
    """Return the authenticated user's data or indicate unauthenticated status."""
    if request.user.is_authenticated:
        return schemas.AuthUserOut.from_orm(request.user)
    return schemas.AnonUserOut(is_authenticated=False)


@router.post("/", auth=None, response=schemas.AuthUserOut | schemas.AnonUserOut)
def login_user(request: HttpRequest, data: AuthUserIn):
    """Log in the user, or return unauthenticated status."""
    if request.user.is_authenticated:
        logout(request)

    user = authenticate(request, **data.dict())
    if user is None:
        return AnonUserOut(is_authenticated=False)

    login(request, user)
    return schemas.AuthUserOut.from_orm(user)


@router.post("/logout", auth=None, response=schemas.AuthUserOut | schemas.AnonUserOut)
def logout_user(request: HttpRequest):
    """Log out the current user and return unauthenticated status."""
    logout(request)
    return schemas.AnonUserOut(is_authenticated=False)
