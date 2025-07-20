import re
from .models import User
from django.core.mail import EmailMessage
from django.conf import settings

def is_valid_email(email: str) -> bool:

    if 'do-not-respond' in email:
        return False

    # Regular expression for a valid email
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))

def is_valid_phone_number(phone: str) -> bool:
    # Remove all spaces from the input
    phone = phone.replace(" ", "")
    
    # Basic E.164 validation: optional +, followed by 10 to 15 digits
    pattern = r'^\+?[1-9]\d{9,14}$'
    return bool(re.match(pattern, phone))


def authenticate_credentials(email: str, password: str) -> User | None:

    try:
        user = User.objects.get(email=email)
        if user.check_password(password):
            return user
        return None
    except User.DoesNotExist:
        return None
    
def send_activation_email(verification_code: str, email: str):

    email_message = EmailMessage(
        "Activate your account",
        f"Activate your account using the code: {verification_code}.",
        settings.EMAIL_HOST_USER,
        [email]
    )

    email_message.fail_silently = True
    email_message.send()