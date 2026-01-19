from django.contrib import admin
from django.urls import path, include
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Definicja schematu Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Software engineering lab",
        default_version='v1',
        description="API documentation for the lab",
    ),
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('medtrackerapp.urls')),  # Włączamy routery aplikacji

    # Swagger UI pod /api/swagger/
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
