from sqlalchemy import create_engine, String, Integer, Boolean, ForeignKey, text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

# DATABASE

DATABASE_URL = "sqlite:///rental.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# BASE MODEL

class Base(DeclarativeBase):
    pass


# USER TABLE

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True
    )

    email: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    password: Mapped[str] = mapped_column(
        String(255)
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="user"
    )

    properties = relationship(
        "Property",
        back_populates="owner",
        foreign_keys="[Property.owner_id]"
    )


# PROPERTY TABLE

class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    title: Mapped[str] = mapped_column(
        String(100)
    )

    location: Mapped[str] = mapped_column(
        String(100)
    )

    price: Mapped[int] = mapped_column(
        Integer
    )

    description: Mapped[str] = mapped_column(
        String(500)
    )

    available: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    owner = relationship(
        "User",
        back_populates="properties",
        foreign_keys=[owner_id]
    )
    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    rented_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    rented_by = relationship(
        "User",
        foreign_keys=[rented_by_id]
    )

    bedrooms: Mapped[int] = mapped_column(
        Integer,
        default=2,
        nullable=True
    )

    bathrooms: Mapped[int] = mapped_column(
        Integer,
        default=2,
        nullable=True
    )

    area: Mapped[int] = mapped_column(
        Integer,
        default=1200,
        nullable=True
    )

    amenities: Mapped[str] = mapped_column(
        String(500),
        default="Air Conditioning, Wifi, Gym",
        nullable=True
    )

    reviews = relationship(
        "Review",
        back_populates="property",
        cascade="all, delete-orphan"
    )


# REVIEW TABLE

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id")
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    rating: Mapped[int] = mapped_column(
        Integer
    )

    comment: Mapped[str] = mapped_column(
        String(500)
    )

    created_at: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )

    property = relationship(
        "Property",
        back_populates="reviews"
    )

    user = relationship(
        "User"
    )


# MAINTENANCE REQUEST TABLE

class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id")
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    issue_description: Mapped[str] = mapped_column(
        String(500)
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="Pending"
    )

    created_at: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )

    property = relationship(
        "Property"
    )

    tenant = relationship(
        "User"
    )


# CREATE TABLES

Base.metadata.create_all(bind=engine)

# Start migration: Add rented_by_id and specifications to properties table if not present
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE properties ADD COLUMN rented_by_id INTEGER REFERENCES users(id)"))
        conn.commit()
    except Exception:
        pass

    for col, col_type in [
        ("bedrooms", "INTEGER DEFAULT 2"),
        ("bathrooms", "INTEGER DEFAULT 2"),
        ("area", "INTEGER DEFAULT 1200"),
        ("amenities", "VARCHAR(500) DEFAULT 'Air Conditioning, Wifi, Gym'")
    ]:
        try:
            conn.execute(text(f"ALTER TABLE properties ADD COLUMN {col} {col_type}"))
            conn.commit()
        except Exception:
            pass