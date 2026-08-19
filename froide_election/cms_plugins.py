from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import Election


@plugin_pool.register_plugin
class UpcomingElectionsPlugin(CMSPluginBase):
    module = _("Elections")
    name = _("Upcoming elections")
    render_template = "froide_election/plugins/upcoming_elections.html"

    def render(self, context, instance, placeholder):
        context = super().render(context, instance, placeholder)
        now = timezone.now()
        too_far = now + timedelta(days=240)
        elections = Election.objects.filter(date__gte=now, date__lte=too_far).order_by(
            "date"
        )
        context["elections"] = elections
        return context


@plugin_pool.register_plugin
class ElectionRegionSearchPlugin(CMSPluginBase):
    module = _("Elections")
    name = _("Election region search")
    render_template = "froide_election/plugins/region_search.html"

    def render(self, context, instance, placeholder):
        context = super().render(context, instance, placeholder)
        context["search_url"] = reverse("election:region-search")
        return context
