"""Schemas for the people app."""

from typing import Annotated, Literal

from ninja import Field, ModelSchema, Schema
from pydantic import EmailStr

from .models import User


class AuthUserOut(ModelSchema):
    """Response of the "me" endpoints when the user is authenticated."""

    type: Literal["authenticated"] = "authenticated"

    class Meta:
        """Pydantic configuration for AuthUserOut schema."""

        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
        )


class AnonUserOut(Schema):
    """Response of the "me" endpoints when the user is not authenticated."""

    type: Literal["anonymous"] = "anonymous"


# The `type` field tells both cases apart: it becomes a discriminator in the
# OpenAPI schema, so that the generated TypeScript client gets a proper
# tagged union (`me.type === "authenticated"` narrows the type).
Me = Annotated[AuthUserOut | AnonUserOut, Field(discriminator="type", title="Me")]


class AuthUserIn(Schema):
    """Request schema for the auth endpoint."""

    email: EmailStr
    password: str
