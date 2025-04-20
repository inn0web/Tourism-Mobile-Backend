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
from .utils import Feed

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
def all_cities(request):
    cities = City.objects.all()
    serializer = CitySerializer(cities, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'city_id',
            openapi.IN_PATH,
            description="ID of the city to retrieve user-specific places for.",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "recommended": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "name": openapi.Schema(type=openapi.TYPE_STRING),
                            "place_id": openapi.Schema(type=openapi.TYPE_STRING),
                            "tag": openapi.Schema(type=openapi.TYPE_STRING),
                            "city_name": openapi.Schema(type=openapi.TYPE_STRING),
                            "image": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI),
                            "rating": openapi.Schema(type=openapi.TYPE_NUMBER, format="float"),
                        }
                    )
                ),
                "popular": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "name": openapi.Schema(type=openapi.TYPE_STRING),
                            "place_id": openapi.Schema(type=openapi.TYPE_STRING),
                            "tag": openapi.Schema(type=openapi.TYPE_STRING),
                            "city_name": openapi.Schema(type=openapi.TYPE_STRING),
                            "image": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI),
                            "rating": openapi.Schema(type=openapi.TYPE_NUMBER, format="float"),
                        }
                    )
                ),
            }
        ),
        404: openapi.Response(
            description="City not found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(type=openapi.TYPE_STRING, example="error"),
                    "message": openapi.Schema(type=openapi.TYPE_STRING, example="City not found")
                }
            )
        ),
        401: openapi.Response(
            description="Unauthorized"
        )
    },
    operation_summary="Get User Feed",
    operation_description="Returns a categorized list of places ('recommended' and 'popular') based on the user's interests and the specified city.",
    tags=['Places']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_feed(request, city_id):

    try:
        city = City.objects.get(id=city_id)
    except City.DoesNotExist:
        return Response({
            "status": "error",
            "message": "City not found"
        }, status=status.HTTP_404_NOT_FOUND)

    user = request.user

    get_user_feed = Feed().get_places_from_google_maps(
        city_name=city.name,
        city_location=(city.latitude, city.longitude),
        user_interests=user.interests.values_list('name', flat=True)
    )

    return Response(get_user_feed, status=status.HTTP_200_OK)