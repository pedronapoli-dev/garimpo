from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.dialects import sqlite
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    query_expression,
    relationship,
)

# Predictable constraint names. Alembic needs them to alter tables in SQLite.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# SQLite has no datetime type: it stores and compares timestamps as text.
# CURRENT_TIMESTAMP writes "2026-11-21 19:18:35", while SQLAlchemy would bind
# Python datetimes as "2026-11-21 19:18:35.000000". Comparing the two as text
# breaks the feed cursor, so both sides use the database's format.
Timestamp = DateTime().with_variant(
    sqlite.DATETIME(
        storage_format=(
            "%(year)04d-%(month)02d-%(day)02d %(hour)02d:%(minute)02d:%(second)02d"
        )
    ),
    "sqlite",
)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class RecommendationType(StrEnum):
    ARTIST = "artist"
    ALBUM = "album"
    TRACK = "track"


recommendation_tags = Table(
    "recommendation_tags",
    Base.metadata,
    Column(
        "recommendation_id",
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("tag_id", ForeignKey("tags.id", ondelete="RESTRICT"), primary_key=True),
)


class Vote(Base):
    """Rule 4: the composite key allows one vote per user per recommendation."""

    __tablename__ = "votes"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True
    )
    # Indexed on its own: vote counts look votes up by recommendation, and the
    # primary key index starts with user_id.
    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )


class Save(Base):
    """Saved to listen later (FR6)."""

    __tablename__ = "saves"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True
    )
    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"), primary_key=True
    )


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(50))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(Timestamp, server_default=func.now())
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="author"
    )


class Invite(Base):
    """Rule 1: sign-up needs an invite, and each invite works once."""

    __tablename__ = "invites"
    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    # UNIQUE: one user is created by at most one invite.
    used_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), unique=True
    )
    used_at: Mapped[datetime | None] = mapped_column(Timestamp)


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    type: Mapped[RecommendationType] = mapped_column(
        Enum(
            RecommendationType,
            name="type",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda enum: [member.value for member in enum],
        )
    )
    artist: Mapped[str] = mapped_column(String(200))
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    artist_key: Mapped[str] = mapped_column(String(200))
    title_key: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    text: Mapped[str] = mapped_column(Text)
    hidden: Mapped[bool] = mapped_column(default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(Timestamp, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        Timestamp, server_default=func.now(), onupdate=func.now()
    )
    author: Mapped["User"] = relationship(back_populates="recommendations")
    # The join table has no position column, so genres are always alphabetical.
    tags: Mapped[list["Tag"]] = relationship(
        secondary=recommendation_tags, order_by="Tag.name"
    )
    # Not columns: each query fills them in with with_expression(), computed in
    # SQL for the user making the request (see services/recommendations.py).
    vote_count: Mapped[int] = query_expression()
    voted_by_me: Mapped[bool] = query_expression()
    saved_by_me: Mapped[bool] = query_expression()
    __table_args__ = (
        UniqueConstraint("type", "artist_key", "title_key"),
        CheckConstraint("length(text) BETWEEN 80 AND 1000", name="text_length"),
        Index("ix_recommendations_created_at_id", "created_at", "id"),
    )
