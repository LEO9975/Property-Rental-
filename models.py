from sqlalchemy import create_engine, String, Integer, Boolean, ForeignKey
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
        back_populates="owner"
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
        back_populates="properties"
    )


# CREATE TABLES

Base.metadata.create_all(bind=engine)