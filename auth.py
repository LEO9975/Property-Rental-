import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from datetime import datetime, timedelta

# SECRET KEY

SECRET_KEY = "property_rental_secret_key"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60


# PASSWORD HASHING

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# HASH PASSWORD

def hash_password(password: str):

    return pwd_context.hash(password)


# VERIFY PASSWORD

def verify_password(
        plain_password,
        hashed_password
):

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# CREATE JWT TOKEN

def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=60)

    to_encode.update({
        "exp": expire
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

# VERIFY JWT TOKEN

def verify_token(token: str):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload.get("sub")

    except InvalidTokenError:

        return None