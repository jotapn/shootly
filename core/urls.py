from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path("auth/", include("accounts.urls")),
    path("webhooks/", include("plans.urls")),
    path("", include("clients.urls")),
    path("", include("orcamentos.urls")),
    path("", include("jobs.urls")),
    path("", include("contracts.urls")),
    path("", include("deliveries.urls")),
    path("", include("payments.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG and settings.HAS_DEBUG_TOOLBAR:
    urlpatterns = [path("__debug__/", include("debug_toolbar.urls"))] + urlpatterns

