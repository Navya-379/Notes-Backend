from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def home(request):
    return JsonResponse({"message": "Notes API running"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.notes.urls")),
    path("", home),
]
