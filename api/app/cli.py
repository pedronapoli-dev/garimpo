"""Management commands. Run from api/: uv run python -m app.cli <command>"""

import argparse

from app.db import SessionLocal
from app.services import invites, users


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "create-invite",
        help="Print a new invite from the dev curator, to sign up the first user.",
    )
    parser.parse_args(argv)

    with SessionLocal() as session:
        invite = invites.create_invite(session, users.get_dev_curator(session))
        print(invite.code)


if __name__ == "__main__":
    main()
