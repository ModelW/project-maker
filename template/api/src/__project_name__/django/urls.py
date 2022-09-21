from django.contrib import admin
from django.urls import path
from hello.views import hello, HelloPdf

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", hello),
    path("pdf/", HelloPdf.as_view()),
]
