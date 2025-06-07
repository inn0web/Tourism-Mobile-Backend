from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.core.mail import EmailMessage

ACCOUNT_VERIFICATION = "ACCOUNT VERIFICATION"
PASSWORD_RESET = "PASSWORD RESET"

VERIFICATION_CODE_TYPES = (
    (ACCOUNT_VERIFICATION, ACCOUNT_VERIFICATION),
    (PASSWORD_RESET, PASSWORD_RESET)
)
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    icon = models.CharField(max_length=225, null=True, blank=True)

    def __str__(self):
        return self.name

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True, help_text="The user's unique email address.")
    first_name = models.CharField(max_length=30, default='', null=True, blank=True, help_text="The user's first name.")
    last_name = models.CharField(max_length=30, default='', null=True, blank=True, help_text="The user's last name.")
    
    phone = models.CharField(max_length=15, default='', null=True, blank=True, help_text="The user's phone number.")
    profile_image = models.FileField(null=True, blank=True, upload_to='Eurotrip/users/', help_text="User's profile image")
    interests = models.ManyToManyField(Category, blank=True, help_text="The user's interests")

    language = models.CharField(max_length=30, default='en', help_text="The user's preferred language. Defaults to 'en' (English).")
    notification_enabled = models.BooleanField(default=False)

    is_staff =  models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False, help_text="Indicates whether the user has all admin permissions. Defaults to False.")
    is_active = models.BooleanField(default=False, help_text="Indicates whether the user account is active. Defaults to False and user needs to verify email on signup before it can be set to True.")
    date_joined = models.DateTimeField(auto_now_add=True, help_text="The date and time when the user joined.")
    
    def __str__(self):
        return self.email
    
    def user_profile_image(self):
    
        if self.profile_image:
            return self.profile_image.url
        
        return "https://res.cloudinary.com/the-proton-guy/image/upload/v1660906962/6215195_0_pjwqfq.webp"
        
    def auth_tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }
    
    def send_email(self, verification_code, code_type):

        if code_type == PASSWORD_RESET:
            
            email_message = EmailMessage(
                "Your Password Reset Code",
                f"Your password reset code is {verification_code}.",
                settings.EMAIL_HOST_USER,
                [self.email]
            )
        elif code_type == ACCOUNT_VERIFICATION:

            email_message = EmailMessage(
                "Activate your account",
                f"Activate your account using the code: {verification_code}.",
                settings.EMAIL_HOST_USER,
                [self.email]
            )

        email_message.fail_silently = True
        email_message.send()

            

    def get_user_threads(self):
        from AiGuide.models import Thread
        return Thread.objects.filter(user=self).order_by('-created_when')


    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['email']

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class VerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    code_type = models.CharField(max_length=225, choices=VERIFICATION_CODE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return self.created_at >= timezone.now() - timedelta(minutes=10)

    def __str__(self):
        return f"{self.user.email} - {self.code}"
    
class UserSavedPlace(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_places')
    tag = models.CharField(max_length=100, null=True, blank=True)
    city_name = models.CharField(max_length=255)
    place_id = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

class UserSearchHistory(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    search = models.CharField(max_length=300)
    date = models.DateTimeField(auto_now_add=True)