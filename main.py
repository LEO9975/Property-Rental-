from fastapi import FastAPI
from fastapi import Request
from fastapi import Form
from fastapi import Depends
from fastapi import Cookie
from fastapi import HTTPException

from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session
from sqlalchemy import select

from models import SessionLocal
from models import User
from models import Property

from auth import hash_password
from auth import verify_password
from auth import create_access_token
from auth import verify_token


app = FastAPI()

templates = Jinja2Templates(
    directory="templates"
)


# DATABASE SESSION

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# HOME PAGE

@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


# REGISTER

@app.post("/register")
def register_user(
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        role: str = Form(...),
        db: Session = Depends(get_db)
):

    existing_user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if existing_user:

        return {
            "message": "Email already exists"
        }

    new_user = User(
        username=username,
        email=email,
        password=hash_password(password),
        role=role
    )

    db.add(new_user)

    db.commit()

    return RedirectResponse(
        "/",
        status_code=303
    )


# LOGIN

@app.post("/login")
def login_user(
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    if not verify_password(
            password,
            user.password
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid Password"
        )

    token = create_access_token(
        {
            "sub": user.username
        }
    )

    response = RedirectResponse(
        "/dashboard",
        status_code=303
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True
    )

    return response

@app.get(
    "/dashboard",
    response_class=HTMLResponse
)
def dashboard(
        request: Request,
        access_token: str = Cookie(None),
        db: Session = Depends(get_db)
):

    if not access_token:

        return RedirectResponse("/")

    username = verify_token(
        access_token
    )

    if not username:

        return RedirectResponse("/")

    user = db.scalar(
        select(User).where(
            User.username == username
        )
    )

    properties = db.scalars(
        select(Property)
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
            "properties": properties
        }
    )

@app.get("/logout")
def logout():

    response = RedirectResponse(
        "/",
        status_code=303
    )

    response.delete_cookie(
        "access_token"
    )

    return response

@app.get(
    "/create-property",
    response_class=HTMLResponse
)
def create_property_page(
        request: Request,
        access_token: str = Cookie(None),
        db: Session = Depends(get_db)
):

    username = verify_token(
        access_token
    )

    if not username:

        return RedirectResponse("/")

    user = db.scalar(
        select(User).where(
            User.username == username
        )
    )

    if user.role != "admin":

        raise HTTPException(
            status_code=403,
            detail="Only Admin Can Add Property"
        )

    return templates.TemplateResponse(
        request=request,
        name="create_property.html"
    )

@app.post("/create-property")
def create_property(
        title: str = Form(...),
        location: str = Form(...),
        price: int = Form(...),
        description: str = Form(...),
        access_token: str = Cookie(None),
        image_url: str = Form(...),
        db: Session = Depends(get_db)
):

    username = verify_token(
        access_token
    )

    user = db.scalar(
        select(User).where(
            User.username == username
        )
    )

    if user.role != "admin":

        raise HTTPException(
            status_code=403,
            detail="Access Denied"
        )

    property_obj = Property(
        title=title,
        location=location,
        price=price,
        description=description,
        owner_id=user.id,
        image_url=image_url
    )

    db.add(property_obj)

    db.commit()

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )

@app.get(
    "/update-property/{property_id}",
    response_class=HTMLResponse
)
def update_property_page(
        property_id: int,
        request: Request,
        access_token: str = Cookie(None),
        image_url: str = Form(""),
        db: Session = Depends(get_db)
):

    username = verify_token(
        access_token
    )

    user = db.scalar(
        select(User).where(
            User.username == username
        )
    )

    if user.role != "admin":

        raise HTTPException(
            status_code=403,
            detail="Access Denied"
        )

    property_obj = db.get(
        Property,
        property_id
    )

    return templates.TemplateResponse(
        request=request,
        name="update_property.html",
        context={
            "property": property_obj
        }
    )

@app.post(
    "/update-property/{property_id}"
)
def update_property(
        property_id: int,
        title: str = Form(...),
        location: str = Form(...),
        price: int = Form(...),
        image_url: str = Form(...),
        description: str = Form(...),
        access_token: str = Cookie(None),
        db: Session = Depends(get_db)
):

    username = verify_token(
        access_token
    )

    user = db.scalar(
        select(User).where(
            User.username == username
        )
    )

    if user.role != "admin":

        raise HTTPException(
            status_code=403,
            detail="Access Denied"
        )

    property_obj = db.get(
        Property,
        property_id
    )

    property_obj.title = title
    property_obj.location = location
    property_obj.price = price
    property_obj.description = description
    property_obj.image_url = image_url
    

    db.commit()

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )

@app.get("/delete-property/{property_id}")
def delete_property(
        property_id: int,
        access_token: str = Cookie(None),
        db: Session = Depends(get_db)
):

    username = verify_token(
        access_token
    )

    user = db.scalar(
        select(User).where(
            User.username == username
        )
    )

    if user.role != "admin":

        raise HTTPException(
            status_code=403,
            detail="Access Denied"
        )

    property_obj = db.get(
        Property,
        property_id
    )

    if property_obj:

        db.delete(
            property_obj
        )

        db.commit()

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )

@app.get("/rent-property/{property_id}")
def rent_property(
        property_id: int,
        access_token: str = Cookie(None),
        db: Session = Depends(get_db)
):

    username = verify_token(
        access_token
    )

    if not username:
        return RedirectResponse("/")

    user = db.scalar(
        select(User).where(
            User.username == username
        )
    )

    property_obj = db.get(
        Property,
        property_id
    )

    if property_obj:

        property_obj.available = False
        property_obj.rented_by_id = user.id

        db.commit()

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )

@app.get("/unrent-property/{property_id}")
def unrent_property(
        property_id: int,
        access_token: str = Cookie(None),
        db: Session = Depends(get_db)
):

    username = verify_token(
        access_token
    )

    if not username:
        return RedirectResponse("/")

    user = db.scalar(
        select(User).where(
            User.username == username
        )
    )

    property_obj = db.get(
        Property,
        property_id
    )

    if property_obj:
        if user.role == "admin" or property_obj.rented_by_id == user.id or property_obj.rented_by_id is None:
            property_obj.available = True
            property_obj.rented_by_id = None
            db.commit()

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )