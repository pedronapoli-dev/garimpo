from contextlib import nullcontext

import pytest
from sqlalchemy.orm import Session

from app import cli
from app.models import Invite, User


def test_create_invite_prints_code_from_dev_curator(
    session: Session,
    curator: User,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "SessionLocal", lambda: nullcontext(session))

    cli.main(["create-invite"])

    code = capsys.readouterr().out.strip()
    assert session.get_one(Invite, code).created_by_id == curator.id


def test_unknown_command_exits_with_usage_error() -> None:
    with pytest.raises(SystemExit) as error:
        cli.main(["nope"])

    assert error.value.code == 2
