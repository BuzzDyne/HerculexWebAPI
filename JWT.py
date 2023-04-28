from datetime import datetime, timedelta
import time
from jose import JWTError, jwt

from _cred import AuthSecret

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=AuthSecret["ACCESS_TOKEN_EXPIRE_MINUTES"])
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, AuthSecret["SECRET_KEY"], algorithm=AuthSecret["ALGORITHM"])
    return encoded_jwt

def decode_token(token: str):
    decode_token = jwt.decode(token, AuthSecret["SECRET_KEY"], algorithm=AuthSecret["ALGORITHM"])
    return decode_token #if decode_token['exp'] >= datetime.utcnow() else None

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, AuthSecret["SECRET_KEY"], algorithms=[AuthSecret["ALGORITHM"]])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception