from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import User, VerificationCode, Category, UserSavedPlace, UserSearchHistory, ACCOUNT_VERIFICATION, PASSWORD_RESET
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
from .utils import is_valid_email, authenticate_credentials, is_valid_phone_number, send_activation_email
from .serializers import UserSerializer, CategorySerializer, UserSearchHistorySerializer
from django.utils.crypto import get_random_string
from Places.models import City
from Places.utils import Feed

@swagger_auto_schema(
    method='post',
    operation_description="Register a new user by providing the required fields. After which user will be required to activate their account",
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
                    "message": "Activate account with code sent to your email",
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
    tags=["User"]
)
@api_view(['POST'])
def register_user(request):

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

    if phone and not is_valid_phone_number(phone):
        return Response({
            "status": "error",
            "message": "Invalid phone number entered"
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

    verification_code = get_random_string(length=6, allowed_chars='0123456789')
    
    # save user data in session
    request.session["user_registration_data"] = {
        email: {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "password": password,
            "code": verification_code
        }
    }

    print(request.session["user_registration_data"])

    # send email to user
    send_activation_email(verification_code, email)

    response = {
        "status": "success",
        "message": "Activate account with code sent to your email",
    }

    return Response(response, status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    method='post',
    operation_description="Request a verification code to activate user account",
    operation_summary="Request Account Activation Code",
    tags=['Account Activation'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email'],
        properties={
            'email': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_EMAIL,
                description='User email address',
                example='user@example.com'
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="Activation code sent successfully",
            examples={
                'application/json': {
                    "status": "success",
                    "message": "Activation code has been sent to your email"
                }
            }
        ),
        400: openapi.Response(
            description="Bad request - Invalid email or user not found",
            examples={
                'application/json': 
                    {
                        "status": "error",
                        "message": "Some error message"
                    }
                
            }
        )
    }
)
@api_view(['POST'])
def request_account_activation_verification_code(request):
 
    email = request.data.get('email')

    # verify data
    if not (email and is_valid_email(email)):
        return Response({
            "status": "error",
            "message": "A valid email must be provided"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)

        new_code = VerificationCode.objects.create(
            user=user,
            code=get_random_string(length=6, allowed_chars='0123456789'),
            code_type=ACCOUNT_VERIFICATION
        )

        user.send_email(verification_code=new_code.code, code_type=ACCOUNT_VERIFICATION)
        
        return Response({
            "status": "success",
            "message": "Activation code has been sent to your email"
        }, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        return Response({
            "status": "error",
            "message": "No user with this email exists"
        }, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_description="Activate user account using verification code sent to email",
    operation_summary="Activate User Account",
    tags=['Account Activation'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email', 'code'],
        properties={
            'code': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='6-digit verification code sent to email',
                example='123456',
                min_length=6,
                max_length=6
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="Account activated successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, example='Account verified successfully'),
                    'user': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                            'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='User email'),
                            'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='User first name'),
                            'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='User last name'),
                            'phone': openapi.Schema(type=openapi.TYPE_STRING, description='User phone number'),
                            'interests': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                                        'description': openapi.Schema(type=openapi.TYPE_STRING)
                                    }
                                ),
                                description='User interests/categories'
                            ),
                            'language': openapi.Schema(type=openapi.TYPE_STRING, description='User preferred language'),
                            'notification_enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Notification preference'),
                            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Account activation status'),
                            'date_joined': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Account creation date'),
                            'profile_image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description='User profile image URL')
                        }
                    ),
                    'tokens': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
                            'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token')
                        }
                    )
                }
            ),
            examples={
                'application/json': {
                    "status": "success",
                    "message": "Account activated successfully",
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "phone": "+1234567890",
                        "interests": [],
                        "language": "en",
                        "notification_enabled": True,
                        "is_active": False,
                        "date_joined": "2024-01-15T10:30:00Z",
                        "profile_image": "https://example.com/media/profile_images/user_1.jpg"
                    },
                    "tokens": {
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                    }
                }
            }
        ),
        400: openapi.Response(
            description="Bad request - Various validation errors",
            examples={
                'application/json': 
                    {
                        "status": "error",
                        "message": "Some error message"
                    },
            }
        )
    }
)
@api_view(['POST'])
def save_and_activate_user_account_after_signup(request):

    # grab payload containing code
    user_entered_code = request.data.get('code')
    email = request.data.get('email')

    if not user_entered_code and email:
        return Response({
            "status": "error",
            "message": "Email and verification code are required"
        }, status=status.HTTP_400_BAD_REQUEST)


    # grab user registration data from session
    registration_data = request.session.get("user_registration_data")

    print(registration_data)

    # check if user registration data exists in session
    if email not in registration_data:
        return Response({
            "status": "error",
            "message": "No user registration data found in session. Please register again."
        }, status=status.HTTP_400_BAD_REQUEST)

    registration_data = registration_data[email]
    
    email = registration_data.get('email')
    code = registration_data.get('code')
    first_name = registration_data.get('first_name')
    last_name = registration_data.get('last_name')
    phone = registration_data.get('phone')
    password = registration_data.get('password')
    
    if code == user_entered_code:

    # create new user object
        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            password=password,
            is_active=True
        )   
        user_serializer = UserSerializer(user)

        response = {
            "status": "success",
            "message": "Account activated successfully",
            "user": user_serializer.data,
            "tokens": user.auth_tokens()
        }

        # clear session data after use
        request.session.pop("user_registration_data", None)  

        return Response(response, status=status.HTTP_200_OK)

    else:
        return Response({
            "status": "error",
            "message": "Invalid verification code provided"
        }, status=status.HTTP_400_BAD_REQUEST)

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
                                'interests': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    description="User's interests as a list of categories",
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Interest Name'),
                                        }
                                    )
                                ),
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
        tags=["User"],
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
            status=status.HTTP_400_BAD_REQUEST)

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
        tags=["User"]
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
    tags=["User"]
)
@api_view(['POST'])
def logout_user(request):
    
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
    tags=["User"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
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
    tags=["User"]
)
@api_view(['POST'])
def request_reset_code(request):
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
        VerificationCode.objects.filter(user=user).delete()

        code = get_random_string(length=6, allowed_chars='0123456789')
        VerificationCode.objects.create(
            user=user, 
            code=code, 
            code_type=PASSWORD_RESET
        )

        # send password reset code to user's email
        user.send_email(password_reset_code=code, code_type=PASSWORD_RESET)

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
    operation_summary="Verify Reset Code",
    tags=["User"]
)
@api_view(['POST'])
def verify_reset_code(request):

    email = request.data.get('email')
    code = request.data.get('code')

    try:
        user = User.objects.get(email=email)
        reset_code = VerificationCode.objects.get(user=user, code=code)

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
    
    except VerificationCode.DoesNotExist:
        return Response({
            "status": "error",
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
    tags=["User"]
)
@api_view(['POST'])
def reset_password(request):

    email = request.data.get('email')
    code = request.data.get('code')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')

    try:
        user = User.objects.get(email=email)
        reset_code = VerificationCode.objects.get(code=code, user=user)

        # validate the passwords and reset code

        if not reset_code.is_valid():
            return Response({
                "status": "error",
                "message": "Reset code has expired."
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not reset_code.code_type == "PASSWORD RESET":
            return Response({
                "status": "error",
                "message": "Invalid code entered"
            }, status=status.HTTP_400_BAD_REQUEST)

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
    
    except VerificationCode.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Reset code provided does not exist"
        }, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method='patch',
    operation_description="Update user details such as email, phone, password, profile image, language, or notification settings.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="New first name"),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="New last name"),
            'email': openapi.Schema(type=openapi.TYPE_STRING, description="New email address"),
            'phone': openapi.Schema(type=openapi.TYPE_STRING, description="New phone number"),
            'current_password': openapi.Schema(type=openapi.TYPE_STRING, description="Current password for verification"),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description="New password"),
            'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description="Confirm new password"),
            'profile_image': openapi.Schema(type=openapi.TYPE_FILE, description="New profile image"),
            'language': openapi.Schema(type=openapi.TYPE_STRING, description="Preferred language", default='en'),
            'notification_enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Enable notifications", default=False),
        },
        required=[]
    ),
    responses={
        200: openapi.Response(
            description="Success",
            examples={
                "application/json": {
                    "status": "success",
                    "message": "Email updated successfully"
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "status": "error",
                    "message": "Passwords do not match"
                }
            }
        ),
        403: openapi.Response(
            description="Forbidden",
            examples={
                "application/json": {
                    "status": "error",
                    "message": "Invalid password provided"
                }
            }
        ),
    },
    operation_summary="Update user details",
    tags=["User"]
)    
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user_account(request):

    email = request.data.get('email')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    phone = request.data.get('phone')
    password = request.data.get('password')
    current_password = request.data.get('current_password')
    confirm_password = request.data.get('confirm_password')
    profile_image = request.FILES.get('profile_image')
    language = request.data.get('language', 'en')
    notification_enabled = request.data.get('notification_enabled', False)

    user = request.user

    first_or_last_name_updated = False

    if first_name and first_name != user.first_name:
        user.first_name = first_name
        first_or_last_name_updated = True
    
    if last_name and last_name != user.last_name:
        user.last_name = last_name
        first_or_last_name_updated = True

    # check if first or last names were entered and save user 
    if first_or_last_name_updated:
        user.save()

        return Response({
            "status": "success",
            "message": "Name updated successfully"
        }, status=status.HTTP_200_OK)

    if email and email != user.email:

        if not is_valid_email(email):
            return Response({
                "status": "error",
                "message": "Invalid email address provided"
            }, status=status.HTTP_400_BAD_REQUEST)

        user.email = email
        user.save()

        return Response({
            "status": "success",
            "message": "Email updated successfully"
        }, status=status.HTTP_200_OK)
    
    if phone and phone != user.phone:

        if not is_valid_phone_number(phone):
            return Response({
                "status": "error",
                "message": "Invalid phone number entered"
            }, status=status.HTTP_400_BAD_REQUEST)

        user.phone = phone
        user.save()

        return Response({
            "status": "success",
            "message": "Phone updated successfully"
        }, status=status.HTTP_200_OK)
    

    if language and language != user.language:
        user.language = language
        user.save()

        return Response({
            "status": "success",
            "message": "Language updated successfully"
        }, status=status.HTTP_200_OK)
    

    if notification_enabled != user.notification_enabled:
        user.notification_enabled = notification_enabled
        user.save()

        return Response({
            "status": "success",
            "message": "Notification updated successfully"
        }, status=status.HTTP_200_OK)
    

    if password and confirm_password and current_password:

        if not user.check_password(current_password):
            return Response({
                "status": "error",
                "message": "Invalid password provided"
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
        
        user.set_password(password)
        user.save()

        return Response({
            "status": "success",
            "message": "Password updated successfully"
        }, status=status.HTTP_200_OK)
    
    if profile_image:
        user.profile_image = profile_image
        user.save()

        return Response({
            "status": "success",
            "message": "Profile image updated successfully"
        }, status=status.HTTP_200_OK)
    
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a list of interests/categories that can be explored.",
    responses={
        200: openapi.Response(
            description="List of interests/categories",
            schema=CategorySerializer(many=True)
        ),
    },
    operation_summary="All Interests/Categories",
    tags=["User"]
)
@api_view(['GET'])
def all_interests(request):

    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='patch',
    operation_summary="Update user interests",
    operation_description="""
    Allows an authenticated user to update their interests by providing a list of category names. 
    The endpoint will replace the user's current interests with the provided ones.
    
    - **Only authenticated users can access this endpoint.**
    - **Categories should be provided as a list of strings.**
    - **If a category does not exist, it will be ignored.**
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'interests': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="A list of interest names that the user wants to set as their preferences.",
                items=openapi.Schema(type=openapi.TYPE_STRING)
            ),
        },
        required=['interests']
    ),
    responses={
        200: openapi.Response(
            description="User interests updated successfully.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(type=openapi.TYPE_STRING, example="success"),
                    "message": openapi.Schema(type=openapi.TYPE_STRING, example="User interests updated successfully."),
                    "user": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "email": openapi.Schema(type=openapi.TYPE_STRING, example="user@example.com"),
                            "first_name": openapi.Schema(type=openapi.TYPE_STRING, example="John"),
                            "last_name": openapi.Schema(type=openapi.TYPE_STRING, example="Doe"),
                            "phone": openapi.Schema(type=openapi.TYPE_STRING, example="123456789"),
                            "is_active": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                            "date_joined": openapi.Schema(type=openapi.TYPE_STRING, format="date-time", example="2024-03-20T10:00:00Z"),
                            "profile_image": openapi.Schema(type=openapi.TYPE_STRING, example="https://yourcdn.com/user_images/123.jpg"),
                            "interests": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                description="List of user's updated interests.",
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "name": openapi.Schema(type=openapi.TYPE_STRING, example="Hiking")
                                    }
                                )
                            ),
                        }
                    )
                }
            )
        ),
        400: openapi.Response(
            description="Invalid request data.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(type=openapi.TYPE_STRING, example="error"),
                    "message": openapi.Schema(type=openapi.TYPE_STRING, example="Invalid format. 'interests' should be a list of category names.")
                }
            )
        ),
        401: openapi.Response(
            description="Authentication required.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(type=openapi.TYPE_STRING, example="error"),
                    "message": openapi.Schema(type=openapi.TYPE_STRING, example="Authentication required.")
                }
            )
        ),
    },
    tags=["User"]
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user_interests(request):
   
    user = request.user
    interest_names = request.data.get('interests', [])

    if not isinstance(interest_names, list) or not all(isinstance(i, str) for i in interest_names):
        return Response({
            "status": "error",
            "message": "Invalid format. 'interests' should be a list of category names."
            }, status=status.HTTP_400_BAD_REQUEST)

    # Fetch matching categories
    categories = Category.objects.filter(name__in=interest_names)

    if not categories.exists():
        return Response({
            "status": "error",
            "message": "No matching interests found."
        }, status=status.HTTP_400_BAD_REQUEST)

    # delete old categories
    user.interests.clear()

    # Update user's interests
    user.interests.set(categories)

    return Response({
        "status": "success",
        "message": "User interests updated successfully",
        "user": UserSerializer(user).data
    }, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='post',
    operation_summary="Save a place for a user",
    operation_description="""
    This endpoint allows an authenticated user to save a place associated with a specific city.
    
    If the place has already been saved by the user, it returns an error message.
    
    - 🔐 Authentication required  
    - `city_id` must refer to a valid City  
    - `place_id` must be included in the request body
    """,
    manual_parameters=[
        openapi.Parameter(
            'city_id',
            openapi.IN_PATH,
            description="ID of the city where the place is located",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['place_id'],
        properties={
            'place_id': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="The unique identifier of the place (Google Place ID)"
            )
        }
    ),
    responses={
        201: openapi.Response(
            description="Place saved successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, example="success"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, example="Place saved successfully")
                }
            )
        ),
        400: openapi.Response(
            description="Place already saved or invalid input",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, example="error"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, example="Place already saved")
                }
            )
        ),
        404: openapi.Response(
            description="City not found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, example="error"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, example="City not found")
                }
            )
        )
    },
    tags=["Places"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_place(request, city_id):

    try:
        city = City.objects.get(id=city_id)
    except City.DoesNotExist:
        return Response({
            "status": "error",
            "message": "City not found"
        }, status=status.HTTP_404_NOT_FOUND)

    place_id = request.data.get('place_id')

    user = request.user
    user_saved_place, created = UserSavedPlace.objects.get_or_create(
        user=user,
        city_name=city.name,
        place_id=place_id
    )
    if created:
        return Response({
            "status": "success",
            "message": "Place saved successfully"
        }, status=status.HTTP_201_CREATED)
    else:
        return Response({
            "status": "error",
            "message": "Place already saved"
        }, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='delete',
    operation_summary="Delete a saved place for a user",
    operation_description="""
    This endpoint allows an authenticated user to delete a place they previously saved within a specific city.

    - 🔐 Authentication required  
    - `city_id` must refer to a valid City  
    - `place_id` must be provided in the request body  
    """,
    manual_parameters=[
        openapi.Parameter(
            'city_id',
            openapi.IN_PATH,
            description="ID of the city where the saved place is located",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['place_id'],
        properties={
            'place_id': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="The unique identifier of the place to be deleted"
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="Place deleted successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, example="success"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, example="Place deleted successfully"),
                }
            )
        ),
        404: openapi.Response(
            description="City or saved place not found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, example="error"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, example="Place not found in saved places"),
                }
            )
        ),
    },
    tags=["Places"]
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_saved_place(request, city_id):
    try:
        city = City.objects.get(id=city_id)
    except City.DoesNotExist:
        return Response({
            "status": "error",
            "message": "City not found"
        }, status=status.HTTP_404_NOT_FOUND)

    place_id = request.data.get('place_id')

    user = request.user
    try:
        user_saved_place = UserSavedPlace.objects.get(
            user=user,
            city_name=city.name,
            place_id=place_id
        )
        user_saved_place.delete()
        return Response({
            "status": "success",
            "message": "Place deleted successfully"
        }, status=status.HTTP_200_OK)
    except UserSavedPlace.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Place not found in saved places"
        }, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method='get',
    operation_summary="List a user's saved places",
    operation_description="""
Returns the full details for every place the authenticated user has saved in the given city.

- 🔐 Authentication required  
- `city_id` must refer to an existing City 
- If the user has no saved places, returns an empty list `[]`
""",
    manual_parameters=[
        openapi.Parameter(
            'city_id',
            in_=openapi.IN_PATH,
            description="ID of the city whose saved places to retrieve",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="A list of detailed place objects (possibly empty)",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "place_id": openapi.Schema(type=openapi.TYPE_STRING),
                        "name": openapi.Schema(type=openapi.TYPE_STRING),
                        "address": openapi.Schema(type=openapi.TYPE_STRING),
                        "phone": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="International phone number (optional, might not be available)"
                        ),
                        "rating": openapi.Schema(type=openapi.TYPE_NUMBER, format="float"),
                        "reviews": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "author": openapi.Schema(type=openapi.TYPE_STRING),
                                    "text": openapi.Schema(type=openapi.TYPE_STRING),
                                    "rating": openapi.Schema(type=openapi.TYPE_NUMBER, format="float"),
                                    "author_image": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI),
                                    "publish_time": openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
                                }
                            )
                        ),
                        "photos": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "url": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI)
                                }
                            )
                        ),
                        "opening_hours": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Opening hours (optional, might not be available)"
                        ),
                        "map_directions": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI),
                        "write_a_review_url": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI),
                        "city_name": openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            )
        ),
    },
    tags=["Places"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_saved_places(request, city_id):

    try:
        city = City.objects.get(id=city_id)
    except City.DoesNotExist:
        return Response({
            "status": "error",
            "message": "City not found"
        }, status=status.HTTP_404_NOT_FOUND)
    
    user = request.user
    saved_places = UserSavedPlace.objects.filter(user=user)

    if saved_places.exists():

        user_saved_places = []

        for saved_place in saved_places:
            get_place_by_place_id = Feed().get_place_details(
                place_id=saved_place.place_id,
                city_name = city.name
            )
            if get_place_by_place_id:
                user_saved_places.append(get_place_by_place_id)
    
        return Response(user_saved_places, status=status.HTTP_200_OK)
    
    return Response([], status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve the user's search history",
    operation_summary="Get User Search History",
    tags=['Search History'],
    responses={
        200: openapi.Response(
            description="Search history retrieved successfully",
            schema=UserSearchHistorySerializer(many=True),
            examples={
                'application/json': [
                    {
                        "search": "luxury cars",
                        "date": "2024-01-15T10:30:00Z"
                    },
                    {
                        "search": "budget vehicles",
                        "date": "2024-01-14T09:15:00Z"
                    }
                ]
            }
        ),
        401: openapi.Response(
            description="Authentication required",
            examples={
                'application/json': {
                    "detail": "Authentication credentials were not provided."
                }
            }
        )
    },
    security=[{'Bearer': []}]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_search_history(request):
    """
    Retrieve the last 10 search queries made by the authenticated user,
    ordered by date (most recent first).
    """
    user_search_history = UserSearchHistory.objects.filter(user=request.user).order_by('-date')[:10]
    serializer = UserSearchHistorySerializer(user_search_history, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='delete',
    operation_description="Clear all search history for the authenticated user",
    operation_summary="Clear User Search History",
    tags=['Search History'],
    responses={
        200: openapi.Response(
            description="Search history cleared successfully",
            examples={
                'application/json': {
                    "status": "success",
                    "message": "Search history cleared successfully"
                }
            }
        ),
        401: openapi.Response(
            description="Authentication required",
            examples={
                'application/json': {
                    "detail": "Authentication credentials were not provided."
                }
            }
        )
    },
    security=[{'Bearer': []}],
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_search_history(request):
    """
    Delete all search history records for the authenticated user.
    This action cannot be undone.
    """
    user_search_history = UserSearchHistory.objects.filter(user=request.user)
    user_search_history.delete()

    return Response({
        "status": "success",
        "message": "Search history cleared successfully"
    }, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='delete',
    operation_description="Delete a specific search history record by its ID",
    operation_summary="Delete Single Search History",
    tags=['Search History'],
    manual_parameters=[
        openapi.Parameter(
            'search_id',
            openapi.IN_PATH,
            description="ID of the search history record to delete",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Search history deleted successfully",
            examples={
                'application/json': {
                    "status": "success",
                    "message": "Search history deleted successfully"
                }
            }
        ),
        404: openapi.Response(
            description="Search history not found",
            examples={
                'application/json': {
                    "status": "error",
                    "message": "Search history not found"
                }
            }
        ),
        401: openapi.Response(
            description="Authentication required",
            examples={
                'application/json': {
                    "detail": "Authentication credentials were not provided."
                }
            }
        )
    },
    security=[{'Bearer': []}],
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_a_single_search_history(request, search_id):
    """
    Delete a specific search history record by its ID.
    """
    try:
        search_history = UserSearchHistory.objects.get(id=search_id, user=request.user)
        search_history.delete()
        return Response({
            "status": "success",
            "message": "Search history deleted successfully"
        }, status=status.HTTP_200_OK)
    except UserSearchHistory.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Search history not found"
        }, status=status.HTTP_404_NOT_FOUND)