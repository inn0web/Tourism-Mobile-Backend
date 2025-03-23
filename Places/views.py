from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import City
from .serializers import CitySerializer
from googlemaps import Client
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

gmaps = Client(key=settings.GOOGLE_API_KEY)

@swagger_auto_schema(
    method='get',
    operation_summary="Retrieve all cities",
    operation_description="Fetches a list of all cities along with their latitude and longitude.",
    responses={
        200: openapi.Response(
            description="A list of cities",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "name": openapi.Schema(type=openapi.TYPE_STRING, example="Berat"),
                        "latitude": openapi.Schema(type=openapi.TYPE_NUMBER, format="float", example=40.7053),
                        "longitude": openapi.Schema(type=openapi.TYPE_NUMBER, format="float", example=19.9519),
                    }
                )
            )
        ),
        500: openapi.Response(description="Internal Server Error"),
    },
    tags=['Places']
)
@api_view(['GET'])
def GetCities(request):
    cities = City.objects.all()
    serializer = CitySerializer(cities, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetUserFeed(request):

    ...