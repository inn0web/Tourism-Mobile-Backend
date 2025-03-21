from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import User, PasswordResetCode
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .utils import is_valid_email, authenticate_credentials
from .serializers import UserSerializer

@swagger_auto_schema(
    method='post',
    operation_description="Register a new user by providing the required fields.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='Email address'),
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
            'phone': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description='Password'),
        },
        required=['email', 'first_name', 'last_name', 'password']
    ),
    responses={
        201: openapi.Response(
            description="User registered successfully",
            examples={
                "application/json": {
                    "status": "success",
                    "message": "Account created successfully",
                    "user": {
                        "email": "user@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "phone": "1234567890",
                        "is_active": True,
                        "date_joined": "2024-10-10T12:34:56Z",
                        "profile_image": "https://example.com/profile.jpg",
                    },
                    "tokens": {
                        "access": "jwt_access_token",
                        "refresh": "jwt_refresh_token"
                    }
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "error": "Some error message, e.g. Passwords do not match"
                }
            }
        )
    },
    operation_summary="Register a new user",
)
@api_view(['POST'])
def RegisterUser(request):

    # grab incoming data

    email = request.data.get('email')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    phone = request.data.get('phone')
    password = request.data.get('password')

    # validate data
    
    if not (email and first_name and last_name and password):
        return Response({
            "status": "error",
            "message": "Email, first name, lastname, and password are required fields"
        }, status=status.HTTP_400_BAD_REQUEST)
    

    if not is_valid_email(email):
        return Response({
            "status": "error",
            "message": "Invalid email address provided"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=email).exists():
        return Response({
            "status": "error",
            "message": "Email address already in use"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(password) < 5:
        return Response({
            "status": "error",
            "message": "Password must be at least 5 characters long"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # create user 

    new_user = User(
        username=email,
        email=email,
        first_name=first_name,
        last_name=last_name,
    )
    new_user.set_password(password)
   
    if phone:
        new_user.phone=phone

    new_user.save() 
    
    # return response 
    user_serializer = UserSerializer(new_user)

    response = {
        "status": "success",
        "message": "Account created successfully",
        "user": user_serializer.data,
        "tokens": new_user.auth_tokens()
    }

    return Response(response, status=status.HTTP_201_CREATED)

class LoginUser(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Token obtained successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'tokens': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'access': openapi.Schema(type=openapi.TYPE_STRING, description='Access token'),
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token'),
                            }
                        ),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First Name'),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last Name'),
                                'phone': openapi.Schema(type=openapi.TYPE_STRING, description='Phone Number'),
                                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is Active'),
                                'date_joined': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Date Joined'),
                                'profile_image': openapi.Schema(type=openapi.TYPE_STRING, description='Profile Image Link'),
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized - Account is inactive."),
        },
        operation_description=(
            "Obtain a new access and refresh token pair using valid credentials. The user must have an active account "
            "to successfully log in. Use the Bearer token in the `Authorization` header for accessing endpoints that require authentication."
        ),
        operation_summary="Login - Obtain JWT Token Pair",
        security=[]
    )
    def post(self, request, *args, **kwargs):
       
        email = request.data.get('email')
        password = request.data.get('password')

        # Authenticate user with provided credentials
        user = authenticate_credentials(email=email, password=password)

        if user is None:
            return Response({
                "status": "error",
                "message": "Invalid credentials"
                }, 
            status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({
                "status": "error",
                "message": "Account is inactive. Please verify your email to activate your account."
                }, 
            status=status.HTTP_401_UNAUTHORIZED)

        try:
            response = super().post(request, *args, **kwargs)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        user_serializer = UserSerializer(user)

        response = {
            "tokens": response.data,
            'user': user_serializer.data
        }
        
        return Response(response, status=status.HTTP_200_OK)
    
class MyTokenRefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer

    @swagger_auto_schema(
        request_body=TokenRefreshSerializer,
        responses={
            200: openapi.Response(
                description="Token refresh successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='New access token'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token'),
                    }
                )
            ),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description="Token is blacklisted"),
                        'code': openapi.Schema(type=openapi.TYPE_STRING, description="token_not_valid"),
                    },
                    example={
                        "detail": "Token is blacklisted",
                        "code": "token_not_valid"
                    }
                )
            ),
        },
        operation_description=(
            "Refresh an access token using a valid refresh token. The access token is valid for 3 days, "
            "and the refresh token is valid for 2 weeks (14 days)."
        ),
        operation_summary="Refresh Token",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs) 