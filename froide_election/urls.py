from django.urls import path
from django.utils.translation import pgettext_lazy

from .views import show_election, show_region

app_name = "election"

urlpatterns = [
    path(
        pgettext_lazy("url part", "election/<slug:election_slug>/"),
        show_election,
        name="election",
    ),
    path(
        pgettext_lazy("url part", "in/<int:region_identifier>-<slug:region_slug>/"),
        show_region,
        name="region",
    ),
]
