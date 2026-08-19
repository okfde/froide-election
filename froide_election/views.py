import re
from functools import cache

from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from froide.georegion.models import GeoRegion
from froide.publicbody.models import Category

from .models import Election
from .templatetags.election_tags import region_url
from .utils import get_publicbody_for_region

REGIONS_PER_PAGE = 20

DIGIT_RE = re.compile(r"^\d+$")


def get_regions_context(request, election=None, base_region=None):
    if election:
        regions = election.get_regions().order_by("name")
    elif base_region:
        regions = base_region.get_descendants().exclude(
            region_identifier=base_region.region_identifier
        )
    elif region_identifier := request.GET.get("region"):
        try:
            regions = GeoRegion.objects.get(
                region_identifier=region_identifier
            ).get_descendants()
        except GeoRegion.DoesNotExist as e:
            raise Http404 from e
    else:
        regions = GeoRegion.objects.all()
    regions = regions.filter(kind__in=["admin_cooperation", "borough"]).order_by("name")

    query = request.GET.get("q", "")
    postcodes = None
    if query:
        if DIGIT_RE.match(query):
            postcodes = GeoRegion.objects.filter(
                region_identifier__startswith=query, kind="zipcode"
            )
        if postcodes:
            regions = (
                regions.filter(related__in=postcodes)
                .distinct()
                .prefetch_related(Prefetch("related", queryset=postcodes))
            )
        else:
            regions = regions.filter(name__icontains=query)

    ancestor_kinds = ["state", "district"]
    if election:
        base_region = election.region

    if base_region:
        if base_region.kind == "country":
            ancestor_kinds = ["state", "district"]
        elif base_region.kind == "state":
            ancestor_kinds = ["district"]
        else:
            ancestor_kinds = []

    paginator = Paginator(regions, REGIONS_PER_PAGE)
    page_number = request.GET.get("page", "")
    page_obj = paginator.get_page(page_number)

    paged_regions = list(page_obj.object_list)

    nodes = {(n.path[: GeoRegion.steplen], n.depth) for n in paged_regions}

    ancestor_q = Q()
    for node in nodes:
        ancestor_q |= Q(path__startswith=node[0], depth__lt=node[1])
    ancestors = GeoRegion.objects.filter(ancestor_q).filter(kind__in=ancestor_kinds)
    if election:
        ancestors = ancestors.exclude(name=election.region.name)
    elif base_region:
        ancestors = ancestors.exclude(name=base_region.name)

    ancestors = ancestors.only("name", "path", "depth").order_by()

    for p in paged_regions:
        p.ancestors = sorted(
            (a for a in ancestors if a.path in p.path and a.path != p.path),
            key=lambda x: x.depth,
            reverse=True,
        )

    region_kinds = " / ".join({p.get_kind_display() for p in paged_regions})

    context = {
        "postcodes": postcodes,
        "paginator": paginator,
        "page_obj": page_obj,
        "query": query,
        "regions": paged_regions,
        "region_kinds": region_kinds,
    }

    if request.headers.get("hx-boosted", "") == "true":
        context["template_name"] = "froide_election/includes/_regions.html"
    return context


def show_election(request, election_slug):
    election = get_object_or_404(
        Election.objects.prefetch_related("region"), slug=election_slug
    )

    context = get_regions_context(
        request,
        election=election,
    )
    template_name = context.get("template_name", "froide_election/election.html")

    return render(
        request,
        template_name,
        context
        | {
            "election": election,
        },
    )


def region_search(request):
    context = get_regions_context(request)

    template_name = context.get("template_name", "froide_election/region_search.html")
    return render(request, template_name, context)


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

    reference_regions = (
        region.get_ancestors()
        .filter(kind__in=["state", "district"])
        .order_by("region_identifier")
        .distinct("region_identifier")
    )
    same_sub_regions = region.get_descendants().filter(
        region_identifier=region.region_identifier
    )
    reference_regions = sorted(reference_regions, key=lambda x: x.level, reverse=True)

    elections = Election.objects.get_upcoming_covered_by_region(
        region, same_sub_regions
    )

    organizers = []
    for election in elections:
        organizing_regions = election.find_organizing_region(region, same_sub_regions)
        organizing_region = organizing_regions.first()
        if organizing_region:
            publicbody = get_publicbody_for_region(organizing_region)
            email = ""
            if publicbody:
                email = publicbody.get_email(responsibility=get_postal_vote_category())
            organizers.append((organizing_region, publicbody, email))

    context = {
        "region": region,
        "reference_regions": reference_regions,
        "elections": elections,
        "organizers": organizers,
        "region_search_url": reverse("election:region-search")
        + "?region="
        + region.region_identifier,
    }
    if not organizers:
        context.update(get_regions_context(request, base_region=region))

    return render(request, "froide_election/region.html", context)
