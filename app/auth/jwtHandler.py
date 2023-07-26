import time
import jwt
from decouple import config

JWT_SECRET = config('secret')
JWT_ALGORITHM = config('algorithm')

def create_jwt_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': time.time() + 1800
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return given_token(token)

def given_token(token):
    return {
        'access_token': token
    }

def decode_jwt_token(token):
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=JWT_ALGORITHM)
        return decoded_token if decoded_token['exp'] >= time.time() else False
    except:
        return False