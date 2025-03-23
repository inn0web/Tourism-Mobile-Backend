from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import BlogListSerializer, BlogDetailSerializer
from Places.models import City
from .models import Blog


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'city_name',
            openapi.IN_PATH,
            description="Name of the city to filter blogs",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: BlogListSerializer(many=True),
        404: openapi.Response(
            description="City not found",
            examples={
                "application/json": {
                    "status": "error",
                    "message": "City not found"
                }
            }
        )
    },
    operation_description="Retrieve a list of published blogs by city name.",
    tags=["Blog"],
    operation_summary="Retrieve blogs about a city",
)
@api_view(['GET'])
def get_blogs_by_city(request, city_name):
   
    try:
        get_city_by_name = City.objects.get(name=city_name)
        blogs = Blog.objects.filter(city=get_city_by_name, is_published=True)
        
        serializer = BlogListSerializer(blogs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except City.DoesNotExist:
        return Response({
            "status": "error",
            "message": "City not found"
        }, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'blog_id',
            openapi.IN_PATH,
            description="ID of the blog",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: BlogDetailSerializer(),
        404: openapi.Response(
            description="Blog not found",
            examples={
                "application/json": {
                    "status": "error",
                    "message": "This blog does not exist"
                }
            }
        )
    },
    operation_description="Retrieve details of a specific blog by its ID.",
    tags=["Blog"],
    operation_summary="Details of a specific blog",
)
@api_view(['GET'])
def get_blog_detail(request, blog_id):
    
    try:
        get_blog_by_id = Blog.objects.get(id=blog_id)
        serializer = BlogDetailSerializer(get_blog_by_id)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Blog.DoesNotExist:
        return Response({
            "status": "error",
            "message": "This blog does not exist"
        }, status=status.HTTP_404_NOT_FOUND)
