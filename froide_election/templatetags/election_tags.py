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
