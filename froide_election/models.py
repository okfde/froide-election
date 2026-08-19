import functools
import operator

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from cms.models.fields import PlaceholderRelationField
from cms.utils.placeholder import get_placeholder_from_slot

from froide.georegion.models import GeoRegion

ELECTION_REGION_KIND = "admin_cooperation"


class RegionSelection(models.Model):
    region = models.ForeignKey(GeoRegion, on_delete=models.PROTECT)
    sub_region_kind = models.CharField(
        max_length=30, choices=GeoRegion.KIND_CHOICES, default=ELECTION_REGION_KIND
    )

    def __str__(self):
        return f"{self.get_sub_region_kind_display()} in {self.region.name} ({self.region.get_kind_display()})"

    def get_regions(self):
        return self.region.get_descendants().filter(kind=self.sub_region_kind)


class ElectionManager(models.Manager):
    def get_upcoming(self):
        return self.get_queryset().filter(date__gte=timezone.now())

    def get_upcoming_covered_by_region(
        self,
        region: GeoRegion,
        same_sub_regions: models.QuerySet[GeoRegion] | None = None,
    ):
        region_filter = models.Q(region__in=region.get_ancestors()) | models.Q(
            region=region
        )
        if same_sub_regions:
            region_filter = functools.reduce(
                operator.or_,
                (models.Q(region=r) for r in same_sub_regions),
                region_filter,
            )
        return self.get_upcoming().filter(region_filter)


class Election(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    short_description = models.TextField(blank=True)

    date = models.DateTimeField()
    region = models.ForeignKey(GeoRegion, on_delete=models.PROTECT)

    region_selections = models.ManyToManyField(RegionSelection)

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

    def find_organizing_region(self, region, same_sub_regions):
        region_filter = models.Q(id=region.id)
        region_filter = functools.reduce(
            operator.or_,
            (models.Q(id=r.id) for r in same_sub_regions),
            region_filter,
        )
        return self.get_regions(region_filter)

    def get_regions(self, filter_q=None):
        selections = self.region_selections.all().select_related("region")
        querysets = [s.get_regions() for s in selections]
        if filter_q:
            querysets = [q.filter(filter_q) for q in querysets]
        return GeoRegion.objects.none().union(*querysets)

    def has_region(self, region):
        return self.get_regions().filter(id=region.id).exists()
