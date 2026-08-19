from django.contrib import admin

from .models import Election, RegionSelection


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "date",
        "region",
    )
    prepopulated_fields = {"slug": ("name",)}
    date_hierarchy = "date"
    raw_id_fields = ("region",)

    search_fields = ("name",)


@admin.register(RegionSelection)
class RegionSelectionAdmin(admin.ModelAdmin):
    list_display = (
        "region",
        "sub_region_kind",
    )
    raw_id_fields = ("region",)
    list_filter = ("sub_region_kind",)

    search_fields = ("region__name",)
