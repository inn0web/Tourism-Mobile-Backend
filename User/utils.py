import re
from .models import User

def is_valid_email(email):

    if 'do-not-respond' in email:
        return False

    # Regular expression for a valid email
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(pattern, email):
        return True
    
    return False

def authenticate_credentials(email, password):

    try:
        user = User.objects.get(email=email)
        if user.check_password(password):
            return user
        return None
    except User.DoesNotExist:
        return None