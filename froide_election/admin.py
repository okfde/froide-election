from django.contrib import admin

from .models import Election


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
