import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User, Vote
from app.schemas import VoteOut
from app.services import saves, votes
from app.services.exceptions import OwnRecommendation, RecommendationNotFound
from tests.conftest import make_recommendation, make_user


def count_votes(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(Vote)) or 0


# Rule 4


def test_vote_returns_new_count_and_state(session: Session, curator: User) -> None:
    recommendation = make_recommendation(session, curator)
    voter = make_user(session, email="voter@example.com")

    assert votes.vote(session, voter, recommendation.id) == VoteOut(
        vote_count=1, voted_by_me=True
    )


def test_voting_twice_keeps_one_vote(session: Session, curator: User) -> None:
    recommendation = make_recommendation(session, curator)
    voter = make_user(session, email="voter@example.com")

    votes.vote(session, voter, recommendation.id)
    state = votes.vote(session, voter, recommendation.id)

    assert state.vote_count == 1
    assert count_votes(session) == 1


def test_votes_from_different_users_add_up(session: Session, curator: User) -> None:
    recommendation = make_recommendation(session, curator)
    voters = [
        make_user(session, email=f"voter{index}@example.com") for index in range(3)
    ]
    states = [votes.vote(session, voter, recommendation.id) for voter in voters]

    assert [state.vote_count for state in states] == [1, 2, 3]


def test_vote_on_own_recommendation_raises(session: Session, curator: User) -> None:
    recommendation = make_recommendation(session, curator)

    with pytest.raises(OwnRecommendation):
        votes.vote(session, curator, recommendation.id)

    assert count_votes(session) == 0


def test_unvote_removes_vote(session: Session, curator: User) -> None:
    recommendation = make_recommendation(session, curator)
    voter = make_user(session, email="voter@example.com")
    votes.vote(session, voter, recommendation.id)

    assert votes.unvote(session, voter, recommendation.id) == VoteOut(
        vote_count=0, voted_by_me=False
    )


def test_unvote_without_vote_is_a_no_op(session: Session, curator: User) -> None:
    recommendation = make_recommendation(session, curator)

    assert votes.unvote(session, curator, recommendation.id).vote_count == 0


@pytest.mark.parametrize("action", [votes.vote, votes.unvote, saves.save, saves.unsave])
def test_missing_recommendation_raises_not_found(
    session: Session, curator: User, action: object
) -> None:
    with pytest.raises(RecommendationNotFound):
        action(session, curator, 999)  # type: ignore[operator]


# Saves


def test_save_and_unsave_are_idempotent(session: Session, curator: User) -> None:
    recommendation = make_recommendation(session, curator)

    assert saves.save(session, curator, recommendation.id).saved_by_me is True
    assert saves.save(session, curator, recommendation.id).saved_by_me is True
    assert saves.unsave(session, curator, recommendation.id).saved_by_me is False
    assert saves.unsave(session, curator, recommendation.id).saved_by_me is False
