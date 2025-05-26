from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import City
from .serializers import CitySerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from .utils import Feed
from User.models import Category
from django.conf import settings
from User.models import UserSearchHistory

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
        ),
        openapi.Parameter(
            'categories',
            openapi.IN_QUERY,
            description="Comma-separated list of categories to search for places. If not provided, the user's saved interests will be used. Examlple: `?categories=restaurant,park,museum`",
            type=openapi.TYPE_STRING,
            required=False
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
        401: openapi.Response(description="Unauthorized")
    },
    operation_summary="Get User Feed",
    operation_description="Returns a categorized list of places ('recommended' and 'popular') based on the user's interests and the specified city. If the `categories` query parameter is provided, it will override the user's saved interests.",
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
    
    categories = request.query_params.get('categories')
    
    # get places by selected categories
    if categories:
        try:
            interests = categories.split(',')
        except:
            return Response({
                "status": "error",
                "message": "Category must be passed as parameter in the format: caregory1,category2,category3"
            }, status=status.HTTP_400_BAD_REQUEST)

    # get places via user interests
    else:
        user = request.user
        interests = user.interests.values_list('name', flat=True)

        if not interests:
            # return Response({
            #     "status": "error",
            #     "message": "User has no interests selected"
            # }, status=status.HTTP_400_BAD_REQUEST)

            # use default interests from settings
            interests = settings.DEFAULT_PLACE_CATEGORIES
        
    get_user_feed = Feed().get_places_from_google_maps(
        city_name=city.name,
        city_location=(city.latitude, city.longitude),
        user_interests=interests
    )

    return Response(get_user_feed, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    tags=['Places'],
    operation_summary="Get Place Details",
    operation_description="Returns detailed information about a place using its Google Maps Place ID, including address, rating, reviews, photos, and Google Maps links.",
    manual_parameters=[
        openapi.Parameter('place_id', openapi.IN_PATH, description="The Google Place ID", type=openapi.TYPE_STRING)
    ],
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'place_id': openapi.Schema(type=openapi.TYPE_STRING),
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'address': openapi.Schema(type=openapi.TYPE_STRING),
                'phone': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="International phone number (optional; may be missing for non-businesses)"
                ),
                'rating': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                'reviews': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description="User reviews (optional; may be missing for non-businesses)",
                        properties={
                            'author': openapi.Schema(type=openapi.TYPE_STRING),
                            'text': openapi.Schema(type=openapi.TYPE_STRING),
                            'rating': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                            'author_image': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                            'publish_time': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                ),
                'photos': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'url': openapi.Schema(type=openapi.TYPE_STRING, format='uri')
                        }
                    )
                ),
                'opening_hours': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'openNow': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'periods': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'open': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'day': openapi.Schema(type=openapi.TYPE_INTEGER),
                                            'hour': openapi.Schema(type=openapi.TYPE_INTEGER),
                                            'minute': openapi.Schema(type=openapi.TYPE_INTEGER),
                                            'date': openapi.Schema(
                                                type=openapi.TYPE_OBJECT,
                                                properties={
                                                    'year': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                    'month': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                    'day': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                }
                                            )
                                        }
                                    ),
                                    'close': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'day': openapi.Schema(type=openapi.TYPE_INTEGER),
                                            'hour': openapi.Schema(type=openapi.TYPE_INTEGER),
                                            'minute': openapi.Schema(type=openapi.TYPE_INTEGER),
                                            'date': openapi.Schema(
                                                type=openapi.TYPE_OBJECT,
                                                properties={
                                                    'year': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                    'month': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                    'day': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                }
                                            )
                                        }
                                    )
                                }
                            )
                        ),
                        'weekdayDescriptions': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING)
                        ),
                        'nextOpenTime': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format='date-time',
                            description="ISO 8601 timestamp of next opening time"
                        )
                    },
                    description="Current opening hours information (optional; only for businesses)"
                ),
                'map_directions': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                'write_a_review_url': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
            }
        ),
        401: 'Unauthorized'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_place_details(request, place_id):

    place_detail = Feed().get_place_details(place_id=place_id)
    return Response(place_detail, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='post',
    operation_summary="Search for recommended and popular places in a city",
    operation_description="""
    Search for places within a given city based on a user's search query and/or selected interests.  
    The results are fetched from the Google Places API and returned in two categories: `recommended` and `popular`.

    - A place is considered **popular** if it has a rating of 4.5 or higher.
    - Other places with lower or no ratings are listed under **recommended**.

    ### Notes:
    - At least one of `search_query` or `interests` must be provided in the request body.
    - The `interests` should be a list of strings matching valid categories in the system.
    - This endpoint uses a `POST` request for flexibility, even though no new data is created.
    - Some fields in the response, like `phone`, `photos`, or `opening_hours`, may be missing depending on whether the place is a registered business or has provided that information to Google.

    ### Example use cases:
    - Search for "parks" or "museums" in a city.
    - Filter results based on user-selected interests like ["restaurants", "art galleries"].
    """,
    tags=['Places'],
    manual_parameters=[
        openapi.Parameter(
            name='city_id',
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            required=True,
            description="The ID of the city to search in."
        )
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=[],
        properties={
            'search_query': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Text-based search term (e.g. 'restaurants', 'parks')."
            ),
            'interests': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
                description="List of user interests (must match existing categories)."
            )
        },
        description="You must provide at least one of `search_query` or `interests`."
    ),
    responses={
        200: openapi.Response(
            description="Successfully fetched popular and recommended places.",
            examples={
                "application/json": {
                    "recommended": [
                        {
                            "name": "Tirana Castle",
                            "place_id": "abcd1234",
                            "tag": "castle",
                            "city_name": "Tirana",
                            "image": "https://maps.googleapis.com/maps/api/place/photo?...",
                            "rating": 4.2
                        }
                    ],
                    "popular": [
                        {
                            "name": "Sky Tower",
                            "place_id": "wxyz5678",
                            "tag": "restaurant",
                            "city_name": "Tirana",
                            "image": "https://maps.googleapis.com/maps/api/place/photo?...",
                            "rating": 4.7
                        }
                    ]
                }
            }
        ),
        400: openapi.Response(description="Invalid format or no matching interests."),
        404: openapi.Response(description="City not found.")
    }
)
@api_view(['POST'])
def search_for_places(request, city_id):

    try:
        city = City.objects.get(id=city_id)
    except City.DoesNotExist:
        return Response({
            "status": "error",
            "message": "City not found"
        }, status=status.HTTP_404_NOT_FOUND)
    
    search_query = request.data.get('search_query', None)
    selected_interests = request.data.get('interests', [])

    if not (search_query or selected_interests):
        return Response({
            "status": "error",
            "message": "Please provide either a search query or interests."
        }, status=status.HTTP_400_BAD_REQUEST)

    user_interests = []

    # add user search query to interests
    if search_query:
        user_interests.append(search_query)

        user = request.user
        if user.is_authenticated:

            # create a new search history entry for user
            history, created = UserSearchHistory.objects.get_or_create(
                user = user,
                search = search_query
            )

    if selected_interests:
        if not isinstance(selected_interests, list) or not all(isinstance(i, str) for i in selected_interests):
            return Response({
                "status": "error",
                "message": "Invalid format. 'interests' should be a list of category names."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch matching categories
        categories = Category.objects.filter(name__in=selected_interests)

       # if categories selected do not exist, make use of default set categories
        if not categories.exists():

            # return Response({
            #     "status": "error",
            #     "message": "No matching interests found."
            # }, status=status.HTTP_400_BAD_REQUEST)

            user_interests = settings.DEFAULT_PLACE_CATEGORIES
        
        else:
            # add selected interests to user_interests
            user_interests.extend(categories.values_list('name', flat=True))

    search_result_based_on_query_and_selected_interests = Feed().get_places_from_google_maps(
        city_name=city.name,
        city_location=(city.latitude, city.longitude),
        user_interests=user_interests
    )

    return Response(
        search_result_based_on_query_and_selected_interests, 
        status=status.HTTP_200_OK
    )