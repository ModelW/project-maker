"""Schemas for the people app."""

from ninja import ModelSchema, Schema
from pydantic import EmailStr

from .models import User


class AuthUserOut(ModelSchema):
    """Response schema of the auth endpoint when the user is authenticated."""

    is_authenticated: bool = True

    class Meta:
        """Pydantic configuration for AuthUserOut schema."""

        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
        )


class AnonUserOut(Schema):
    """Response schema of the auth endpoint when the user is not authenticated."""

    is_authenticated: bool = False


class AuthUserIn(Schema):
    """Request schema for the auth endpoint."""

    email: EmailStr
    password: str
