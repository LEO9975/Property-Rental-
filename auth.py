from jose import JWTError, jwt
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

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


# VERIFY JWT TOKEN

def verify_token(token: str):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")

        if username is None:
            return None

        return username

    except JWTError:

        return None