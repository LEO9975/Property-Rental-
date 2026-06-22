from fastapi import FastAPI, Request, Form, Depends, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session
from sqlalchemy import select

from datetime import datetime
from models import SessionLocal, User, Property, Review, MaintenanceRequest

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)

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

    stats = {}
    maintenance_requests = []
    if user.role == "admin":
        total_properties = len(properties)
        rented_properties = len([p for p in properties if not p.available])
        occupancy_rate = round((rented_properties / total_properties * 100), 1) if total_properties > 0 else 0
        total_revenue = sum(p.price for p in properties if not p.available)
        
        maintenance_requests = db.scalars(
            select(MaintenanceRequest)
            .order_by(MaintenanceRequest.id.desc())
        ).all()
        
        pending_maintenance = len([r for r in maintenance_requests if r.status != "Resolved"])
        
        stats = {
            "total_properties": total_properties,
            "rented_properties": rented_properties,
            "occupancy_rate": occupancy_rate,
            "total_revenue": total_revenue,
            "pending_maintenance": pending_maintenance
        }

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
            "properties": properties,
            "stats": stats,
            "maintenance_requests": maintenance_requests
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
        bedrooms: int = Form(2),
        bathrooms: int = Form(2),
        area: int = Form(1200),
        amenities: str = Form("Air Conditioning, Wifi, Gym"),
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
        image_url=image_url,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        area=area,
        amenities=amenities
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
        bedrooms: int = Form(2),
        bathrooms: int = Form(2),
        area: int = Form(1200),
        amenities: str = Form("Air Conditioning, Wifi, Gym"),
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
    property_obj.bedrooms = bedrooms
    property_obj.bathrooms = bathrooms
    property_obj.area = area
    property_obj.amenities = amenities
    

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

@app.get("/property/{property_id}", response_class=HTMLResponse)
def property_detail(
        property_id: int,
        request: Request,
        access_token: str = Cookie(None),
        db: Session = Depends(get_db)
):
    if not access_token:
        return RedirectResponse("/")

    username = verify_token(access_token)
    if not username:
        return RedirectResponse("/")

    user = db.scalar(
        select(User).where(User.username == username)
    )

    property_obj = db.get(Property, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    reviews = db.scalars(
        select(Review)
        .where(Review.property_id == property_id)
        .order_by(Review.id.desc())
    ).all()
    
    avg_rating = 0
    if reviews:
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
        avg_rating = round(avg_rating, 1)

    maintenance_requests = []
    if user.role == "admin":
        maintenance_requests = db.scalars(
            select(MaintenanceRequest)
            .where(MaintenanceRequest.property_id == property_id)
            .order_by(MaintenanceRequest.id.desc())
        ).all()
    elif property_obj.rented_by_id == user.id:
        maintenance_requests = db.scalars(
            select(MaintenanceRequest)
            .where(
                MaintenanceRequest.property_id == property_id,
                MaintenanceRequest.tenant_id == user.id
            )
            .order_by(MaintenanceRequest.id.desc())
        ).all()

    return templates.TemplateResponse(
        request=request,
        name="property_detail.html",
        context={
            "user": user,
            "property": property_obj,
            "reviews": reviews,
            "avg_rating": avg_rating,
            "maintenance_requests": maintenance_requests
        }
    )

@app.post("/property/{property_id}/review")
def add_property_review(
        property_id: int,
        rating: int = Form(...),
        comment: str = Form(...),
        access_token: str = Cookie(None),
        db: Session = Depends(get_db)
):
    if not access_token:
        return RedirectResponse("/")

    username = verify_token(access_token)
    if not username:
        return RedirectResponse("/")

    user = db.scalar(
        select(User).where(User.username == username)
    )

    review = Review(
        property_id=property_id,
        user_id=user.id,
        rating=rating,
        comment=comment,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    db.add(review)
    db.commit()

    return RedirectResponse(f"/property/{property_id}", status_code=303)

@app.post("/property/{property_id}/maintenance")
def submit_maintenance_request(
        property_id: int,
        issue_description: str = Form(...),
        access_token: str = Cookie(None),
        db: Session = Depends(get_db)
):
    if not access_token:
        return RedirectResponse("/")

    username = verify_token(access_token)
    if not username:
        return RedirectResponse("/")

    user = db.scalar(
        select(User).where(User.username == username)
    )

    property_obj = db.get(Property, property_id)
    if not property_obj or property_obj.rented_by_id != user.id:
        raise HTTPException(status_code=403, detail="Only current tenant can submit maintenance requests")

    req = MaintenanceRequest(
        property_id=property_id,
        tenant_id=user.id,
        issue_description=issue_description,
        status="Pending",
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    db.add(req)
    db.commit()

    return RedirectResponse(f"/property/{property_id}", status_code=303)

@app.post("/maintenance/{request_id}/status")
def update_maintenance_status(
        request_id: int,
        status: str = Form(...),
        access_token: str = Cookie(None),
        db: Session = Depends(get_db)
):
    if not access_token:
        return RedirectResponse("/")

    username = verify_token(access_token)
    if not username:
        return RedirectResponse("/")

    user = db.scalar(
        select(User).where(User.username == username)
    )

    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update maintenance request status")

    req = db.get(MaintenanceRequest, request_id)
    if req:
        req.status = status
        db.commit()

    return RedirectResponse("/dashboard", status_code=303)