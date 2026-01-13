import random
from django.core.cache import cache

OTP_TTL = 300  
def generate_otp():
    return str(random.randint(100000, 999999))



OTP_TTL = 300  # 5 minutes

def set_otp(phone, purpose):
    otp = generate_otp()
    key = f"otp:{phone}:{purpose}"
    value = {"otp": otp}

    cache.set(key, value, timeout=OTP_TTL)

    

    return otp


def get_otp(phone, purpose):
    key = f"otp:{phone}:{purpose}"
    value = cache.get(key)

    

    return value


def delete_otp(phone, purpose):
    key = f"otp:{phone}:{purpose}"
    cache.delete(key)
   
