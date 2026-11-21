import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Recommendation, RecommendationType, Tag, recommendation_tags
from tests.conftest import make_recommendation, make_user


def test_recommendation_with_tags_persists_returns_tags(session: Session) -> None:
    author = make_user(session)
    recommendation = make_recommendation(session, author)
    recommendation.tags = [Tag(name="mpb"), Tag(name="jazz")]
    session.commit()
    session.expunge_all()

    loaded = session.get_one(Recommendation, recommendation.id)

    assert {tag.name for tag in loaded.tags} == {"mpb", "jazz"}
    assert loaded.author.email == author.email


def test_recommendation_defaults_returns_not_hidden_with_timestamps(
    session: Session,
) -> None:
    recommendation = make_recommendation(session, make_user(session))
    session.commit()
    session.refresh(recommendation)

    assert recommendation.hidden is False
    assert recommendation.created_at is not None
    assert recommendation.updated_at is not None


def test_duplicate_type_artist_and_title_raises_integrity_error(
    session: Session,
) -> None:
    make_recommendation(session, make_user(session))
    other_author = make_user(session, email="other@example.com")

    with pytest.raises(IntegrityError):
        make_recommendation(session, other_author)


def test_same_artist_and_title_with_other_type_persists(session: Session) -> None:
    author = make_user(session)
    make_recommendation(session, author, type=RecommendationType.ALBUM)
    make_recommendation(session, author, type=RecommendationType.TRACK)

    types = session.scalars(select(Recommendation.type)).all()
    assert sorted(types) == [RecommendationType.ALBUM, RecommendationType.TRACK]


def test_recommendation_with_missing_author_raises_integrity_error(
    session: Session,
) -> None:
    recommendation = Recommendation(
        author_id=999,
        type=RecommendationType.ARTIST,
        artist="Arthur Verocai",
        artist_key="arthur verocai",
        text="x" * 80,
    )
    session.add(recommendation)

    with pytest.raises(IntegrityError):
        session.flush()


@pytest.mark.parametrize("length", [79, 1001])
def test_text_length_out_of_range_raises_integrity_error(
    session: Session, length: int
) -> None:
    with pytest.raises(IntegrityError):
        make_recommendation(session, make_user(session), text="x" * length)


def test_duplicate_email_raises_integrity_error(session: Session) -> None:
    make_user(session)

    with pytest.raises(IntegrityError):
        make_user(session)


def test_deleting_recommendation_cascades_to_tag_links(session: Session) -> None:
    recommendation = make_recommendation(session, make_user(session))
    recommendation.tags = [Tag(name="mpb")]
    session.flush()

    # Core delete, so the cascade comes from the database and not from the ORM.
    session.execute(delete(Recommendation))

    assert session.scalars(select(recommendation_tags.c.tag_id)).all() == []
    assert session.scalars(select(Tag.name)).all() == ["mpb"]


def test_deleting_tag_in_use_raises_integrity_error(session: Session) -> None:
    recommendation = make_recommendation(session, make_user(session))
    recommendation.tags = [Tag(name="mpb")]
    session.flush()

    with pytest.raises(IntegrityError):
        session.execute(delete(Tag))
