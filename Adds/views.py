from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Advertisement
from .serializers import AdvertisementSerializer
from django.utils import timezone

@swagger_auto_schema(
    method='get',
    operation_summary="Get Active Advertisements",
    responses={
        200: openapi.Response(
            description="List of active advertisements",
            schema=AdvertisementSerializer(many=True)
        )
    },
    tags=['Advertisement']
)
@api_view(['GET'])
def get_active_advertisements(request):
    current_datetime = timezone.now()
    
    advertisements = Advertisement.objects.filter(
        is_active=True,
        end_date__gt=current_datetime,  # End date greater than current time
        start_date__lte=current_datetime  # Start date less than or equal to current time
    ).order_by('-priority')
    
    serializer = AdvertisementSerializer(advertisements, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)