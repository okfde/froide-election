from functools import cache

from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from froide.georegion.models import GeoRegion
from froide.publicbody.models import Category

from .models import Election
from .templatetags.election_tags import region_url
from .utils import get_publicbody_for_region

REGIONS_PER_PAGE = 20


def show_election(request, election_slug):
    election = get_object_or_404(
        Election.objects.select_related("region"), slug=election_slug
    )
    qs = election.get_regions().order_by("name")

    query = request.GET.get("q", "")
    if query:
        qs = qs.filter(name__icontains=query)

    paginator = Paginator(qs, REGIONS_PER_PAGE)
    page_number = request.GET.get("page", "")
    page_obj = paginator.get_page(page_number)

    template_name = "froide_election/election.html"
    if request.headers.get("hx-boosted", "") == "true":
        template_name = "froide_election/includes/_regions.html"

    return render(
        request,
        template_name,
        {
            "election": election,
            "paginator": paginator,
            "page_obj": page_obj,
            "query": query,
            "regions": page_obj.object_list,
        },
    )


@cache
def get_postal_vote_category():
    return Category.objects.filter(name="Briefwahl").first()


def show_region(request, region_identifier, region_slug):
    region = (
        GeoRegion.objects.filter(region_identifier=region_identifier)
        .order_by("level")
        .first()
    )
    if region is None:
        raise Http404
    if region.slug != region_slug:
        return redirect(region_url(region))

    reference_regions = region.get_ancestors().filter(kind__in=["state", "district"])

    elections = Election.objects.get_upcoming_for_region(region)
    publicbody = get_publicbody_for_region(region)
    email = ""
    if publicbody:
        email = publicbody.get_email(responsibility=get_postal_vote_category())

    return render(
        request,
        "froide_election/region.html",
        {
            "region": region,
            "reference_regions": reference_regions,
            "elections": elections,
            "publicbody": publicbody,
            "email": email,
        },
    )
