from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FroideElectionConfig(AppConfig):
    name = "froide_election"
    verbose_name = _("Election App")
