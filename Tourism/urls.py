from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from decouple import config

schema_view = get_schema_view(
   openapi.Info(
      title="Eurotrip API",
      default_version='v1',
      description="Below, you will find all endpoints and documentation to each of these endpoints",
    #   terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="adesolaayodeji53@gmail.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   url=config("SWAGGER_DOCS_BASE_URL"),
)

version = 'v1'

urlpatterns = [
   path('admin/', admin.site.urls),
   path(f'api/{version}/user/', include('User.urls')),
   path(f'api/{version}/places/', include('Places.urls')),
   path(f'api/{version}/blog/', include('Blog.urls')),
   path(f'api/{version}/ai/', include('AiGuide.urls')),
   path(f'api/{version}/adds/', include('Adds.urls')),

   path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

   path("ckeditor5/", include('django_ckeditor_5.urls')),
]
