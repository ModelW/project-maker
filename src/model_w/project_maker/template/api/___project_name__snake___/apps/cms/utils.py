"""Utility functions for the CMS app."""

from logging import getLogger

import httpx
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest
from django.shortcuts import redirect
from wagtail.models import Page

logger = getLogger(__name__)


class PreviewDataStore:
    """
    A class to store the preview data in the request session.

    Methods
    -------
        store_preview_data(request: HttpRequest, app_dot_model: str, data: str)
        get_preview_data(request: HttpRequest) -> tuple[str, str]

    Attributes
    ----------
        DATA_KEY (str): The key to store the preview data in the session.
        MODEL_KEY (str): The key to store the preview model in the session.

    """

    DATA_KEY = "preview_data"
    MODEL_KEY = "preview_model"

    @classmethod
    def store_preview_data(
        cls,
        *,
        request: HttpRequest,
        app_dot_model: str,
        data: str,
    ) -> None:
        """
        Store the preview data in the session so it can be retrieved later
        by the front.

        Args:
        ----
            request (HttpRequest): The request object to store the data in the session.
            app_dot_model (str): The app and model of the preview data.
            data (str): The preview data to be stored in the session (JSON).

        """
        request.session[cls.MODEL_KEY] = app_dot_model
        request.session[cls.DATA_KEY] = data

    @classmethod
    def get_preview_data(cls, request: HttpRequest) -> tuple[str, str]:
        """
        Get the preview data from the session.

        Args:
        ----
            request (HttpRequest): The request object to retrieve the data from the session.

        Returns:
        -------
            tuple[str, str]: A tuple containing the app_dot_model and data.

        """
        app_dot_model = request.session.get(cls.MODEL_KEY, "")
        data = request.session.get(cls.DATA_KEY, "")
        return app_dot_model, data


def content_type_to_app_dot_model(content_type: ContentType) -> str:
    """
    Convert a content type to a string in the format of "app_label.model_name".

    Args:
    ----
        content_type (ContentType): The content type to convert.

    Returns:
    -------
        str: The content type in the format of "app_label.model_name".

    """
    return f"{content_type.app_label}.{content_type.model}"


class ApiPage(Page):
    """
    Adds specific functionality needed for the API and front to
    work together.

    Namely, allowing previews to be served by the front-end.
    """

    def serve_preview(self, request, mode_name=None):
        """
        Make a request to the front-end to retrieve the preview data.

        As Wagtail doesn't have any templates, we instead store the data
        in the session, and redirect to the front-end's preview page.
        The preview page then retrieves the data from the session and
        renders it.
        """
        app_dot_model = content_type_to_app_dot_model(self.content_type)
        PreviewDataStore.store_preview_data(
            request=request,
            app_dot_model=app_dot_model,
            data=self.to_json(),
        )
        redirect_url = httpx.URL(request.build_absolute_uri())
        redirect_url = redirect_url.copy_with(
            params={
                "in_preview_panel": app_dot_model,
            },
        )

        return redirect(str(redirect_url))

    class Meta:
        abstract = True
