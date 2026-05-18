from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from cms.models.fields import PlaceholderRelationField
from cms.utils.placeholder import get_placeholder_from_slot

from froide.georegion.models import GeoRegion

ELECTION_REGION_KIND = "admin_cooperation"


class ElectionManager(models.Manager):
    def get_upcoming_for_region(self, region: GeoRegion):
        regions = list(region.get_ancestors()) + [region]
        return self.get_queryset().filter(date__gte=timezone.now(), region__in=regions)


class Election(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    short_description = models.TextField(blank=True)

    date = models.DateTimeField()
    region = models.ForeignKey(GeoRegion, on_delete=models.PROTECT)
    sub_region_kind = models.CharField(
        max_length=30, choices=GeoRegion.KIND_CHOICES, default=ELECTION_REGION_KIND
    )

    placeholders = PlaceholderRelationField()

    objects = ElectionManager()

    class Meta:
        verbose_name = _("election")
        verbose_name_plural = _("elections")

    def __str__(self):
        return self.name

    @cached_property
    def content(self):
        return get_placeholder_from_slot(self.placeholders, "content")

    def get_absolute_url(self):
        return reverse("election:election", kwargs={"election_slug": self.slug})

    def get_regions(self):
        return self.region.get_descendants().filter(kind=self.sub_region_kind)
