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
from django.utils.crypto import get_random_string

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
    
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'refresh': openapi.Schema(
                type=openapi.TYPE_STRING, 
                description='Refresh token of the current session that needs to be blacklisted.'
            ),
        },
        required=['refresh'],
        example={
            'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
        },
    ),
    responses={
        204: openapi.Response(
            description="Successfully logged out.",
            examples={
                'application/json': {
                    'message': 'Successfully logged out.'
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request",
            examples={
                'application/json': {
                    'error': 'Refresh token is required.'
                }
            }
        ),
    },
    operation_description=(
        "Logs out the current user by invalidating the provided refresh token. This action blacklists the refresh token, "
        "ensuring that it cannot be used to obtain new access tokens in the future. The refresh token must be included "
        "in the request body. If the token is missing or invalid, a 400 Bad Request error will be returned."
    ),
    operation_summary="Logout a user",
)
@api_view(['POST'])
def Logout(request):
    
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token is None:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Blacklist the refresh token to prevent further use
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        return Response({
            "status": "success",
            "message": "Successfully logged out."
            }, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            description="User information retrieved successfully",
            schema=UserSerializer
        ),
        401: openapi.Response(
            description="Unauthorized",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING, description="Error detail"),
                },
                example={
                    "detail": "Authentication credentials were not provided."
                }
            )
        ),
    },
    operation_description="Retrieve the current authenticated user's information.",
    operation_summary="Get User Info",
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetUserInfo(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email address'),
        }
    ),
    responses={
        200: openapi.Response(
            description="Reset code sent successfully",
            examples={
                "application/json": {
                    "status": "success",
                    "message": "Reset code sent successfully",
                }
            }
        ),
        404: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "status": "error",
                    "message": "No user with this email found",
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "status": "error",
                    "message": "Email provided is invalid",
                }
            }
        )
    },
    operation_description="Request a password reset code by entering your email address.",
    operation_summary="Request Password Reset Code",
)
@api_view(['POST'])
def RequestResetCode(request):
    email = request.data.get('email')

    if not email:
        return Response({
            "status": "error",
            "message": "Email address is required"
            }, status=status.HTTP_400_BAD_REQUEST
        )
    
    if not is_valid_email(email):
        return Response({
            "status": "error",
            "message": "Email provided is invalid"
            }, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)

        # delete old codes
        PasswordResetCode.objects.filter(user=user).delete()

        code = get_random_string(length=6, allowed_chars='0123456789')
        PasswordResetCode.objects.create(user=user, code=code)

        # Send email (this is a simple example; configure your email backend as needed)
        user.send_email(password_reset_code=code)

        return Response({
            "status": "success",
            "message": "Reset code sent successfully"
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            "status": "error",
            "message": "No user with this email found"
        }, status=status.HTTP_404_NOT_FOUND)
        
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
            'code': openapi.Schema(type=openapi.TYPE_STRING, description='Reset code sent to email'),
        },
        required=['email', 'code']
    ),
    responses={
        200: openapi.Response(
            description="Password updated successfully",
            examples={
                "application/json": {
                    "status": "success",
                    "message": "Reset code is valid",
                }
            }
        ),
        403: openapi.Response(
            description="Expired Reset Code",
            examples={
                "application/json": {
                    "status": "error",
                    "message": "Reset code has expired",
                },
            }
        ),
        404: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "status": "error",
                    "message": "User with this email does not exist",
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "status": "error",
                    "message": "Invalid reset code",
                }
            }
        )
    },
    operation_description="Verify the reset code sent to the user's email.",
    operation_summary="Verify Reset Code"
)
@api_view(['POST'])
def VerifyResetCode(request):

    email = request.data.get('email')
    code = request.data.get('code')

    try:
        user = User.objects.get(email=email)
        reset_code = PasswordResetCode.objects.get(user=user, code=code)

        if reset_code.is_valid():
            return Response({
                "status": "success",
                "message": "Reset code is valid."
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": "Reset code has expired."
            }, status=status.HTTP_403_FORBIDDEN)

    except User.DoesNotExist:
        return Response({
            "status": "error",
            "message": "User with this email does not exist."
        }, status=status.HTTP_404_NOT_FOUND)
    
    except PasswordResetCode.DoesNotExist:
        return Response({
            "status" "error,"
            "message": "Invalid reset code."
        }, status=status.HTTP_400_BAD_REQUEST)
    
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['code', 'password', 'confirm_password'],
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
            'code': openapi.Schema(type=openapi.TYPE_STRING, description='The reset code sent to the user email.'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='The new password.'),
            'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description='The new password again for confirmation.'),
        },
    ),
    responses={
        200: openapi.Response(
            description="Reset code is valid",
            examples={
                "application/json": {
                    "status": "success",
                    "message": "Password updated successfully",
                }
            }
        ),
        403: openapi.Response(
            description="Expired Reset Code",
            examples={
                "application/json": {
                    "status": "error",
                    "message": "Reset code has expired",
                },
            }
        ),
        404: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "status": "error",
                    "message": "No user with that email address exists",
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "status": "error",
                    "message": "Passwords do not match",
                }
            }
        )
    },
    operation_description="Reset the user's password using the reset code.",
    operation_summary="Reset Password",
)
@api_view(['POST'])
def ResetPassword(request):

    email = request.data.get('email')
    code = request.data.get('code')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')

    try:
        user = User.objects.get(email=email)
        reset_code = PasswordResetCode.objects.get(code=code, user=user)

        # validate the passwords and reset code

        if not reset_code.is_valid():
            return Response({
                "status": "error",
                "message": "Reset code has expired."
            }, status=status.HTTP_403_FORBIDDEN)

        if password != confirm_password:
            return Response({
                "status": "error",
                "message": "Passwords do not match"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(password) < 5:
            return Response({
                "status": "error",
                "message": "Password must be at least 5 characters long"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # update the password

        user.set_password(password)
        user.save()

        reset_code.delete()

        return Response({
            "status": "success",
            "message": "Password updated successfully"
        }, status=status.HTTP_200_OK)


    except User.DoesNotExist:
        return Response({
            "status": "error",
            "message": "No user with that email address exists"
        }, status=status.HTTP_404_NOT_FOUND)
    
    except PasswordResetCode.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Reset code provided does not exist"
        }, status=status.HTTP_404_NOT_FOUND)