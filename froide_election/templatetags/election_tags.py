from django import template
from django.urls import reverse

register = template.Library()


@register.filter
def region_url(region):
    return reverse(
        "election:region",
        kwargs={
            "region_identifier": region.region_identifier,
            "region_slug": region.slug,
        },
    )


@register.filter
def region_ancestors(region):
    # .ancestors is annotated before
    if not hasattr(region, "ancestors"):
        return ""
    ancestors = {a.name: 1 for a in region.ancestors if a.name != region.name}
    return ", ".join(ancestors.keys())
