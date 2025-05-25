import re
from .models import User


def is_valid_email(email):

    if 'do-not-respond' in email:
        return False

    # Regular expression for a valid email
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))

def is_valid_phone_number(phone):
    # Remove all spaces from the input
    phone = phone.replace(" ", "")
    
    # Basic E.164 validation: optional +, followed by 10 to 15 digits
    pattern = r'^\+?[1-9]\d{9,14}$'
    return bool(re.match(pattern, phone))


def authenticate_credentials(email, password):

    try:
        user = User.objects.get(email=email)
        if user.check_password(password):
            return user
        return None
    except User.DoesNotExist:
        return None