from sqlalchemy import DateTime, Float, String, Text, func, BigInteger, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


Base = declarative_base()


class Button(Base):
    __tablename__ = "button"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    url: Mapped[str] = mapped_column(nullable=True)
    callback_data: Mapped[str] = mapped_column(nullable=True)
    type: Mapped[str]


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    settings = mapped_column(JSON, nullable=True)
