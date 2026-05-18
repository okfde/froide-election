from django.utils.translation import gettext_lazy as _

from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool


@apphook_pool.register
class ElectionCMSApp(CMSApp):
    name = _("Election CMS App")
    app_name = "election"

    def get_urls(self, page=None, language=None, **kwargs):
        return ["froide_election.urls"]
