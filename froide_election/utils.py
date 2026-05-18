from froide.publicbody.models import PublicBody

CATEGORIES = ["Briefwahl", "Wahlrecht", "Zentrale Verwaltung"]


def get_publicbody_for_region(region):
    return PublicBody.objects.filter(
        categories__name__in=CATEGORIES, regions=region
    ).first()
