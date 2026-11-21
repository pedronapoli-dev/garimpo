class DomainError(Exception):
    """A business rule violation. main.py maps each subclass to a status code."""

    code = "domain_error"

    def __init__(self, message: str, *, existing_id: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.existing_id = existing_id


class DuplicateRecommendation(DomainError):
    """Rule 7: carries the id of the recommendation that already exists."""

    code = "duplicate_recommendation"

    def __init__(self, existing_id: int) -> None:
        super().__init__(
            "This artist and title were already recommended.",
            existing_id=existing_id,
        )


class RecommendationNotFound(DomainError):
    code = "recommendation_not_found"

    def __init__(self, recommendation_id: int) -> None:
        super().__init__(f"Recommendation {recommendation_id} does not exist.")


class InvalidCursor(DomainError):
    code = "invalid_cursor"

    def __init__(self) -> None:
        super().__init__("The cursor is not valid. Start again from the first page.")


class InvalidRecommendation(DomainError):
    """Rule 2 broken by a partial update, once merged with the stored values."""

    code = "invalid_recommendation"


class NotAuthenticated(DomainError):
    code = "not_authenticated"

    def __init__(self) -> None:
        super().__init__("Log in to do this.")


class InvalidCredentials(DomainError):
    code = "invalid_credentials"

    def __init__(self) -> None:
        super().__init__("Wrong email or password.")


class InvalidInvite(DomainError):
    """Rule 1: the code does not exist or was already used."""

    code = "invalid_invite"

    def __init__(self) -> None:
        super().__init__("This invite code is not valid or was already used.")


class EmailTaken(DomainError):
    code = "email_taken"

    def __init__(self) -> None:
        super().__init__("An account with this email already exists.")


class NotAuthor(DomainError):
    """Rule 5: only the author can edit or delete a recommendation."""

    code = "not_author"

    def __init__(self) -> None:
        super().__init__("Only the author can change this recommendation.")


class OwnRecommendation(DomainError):
    """Rule 4: users cannot vote on their own recommendations."""

    code = "own_recommendation"

    def __init__(self) -> None:
        super().__init__("You cannot vote on your own recommendation.")


class UserNotFound(DomainError):
    code = "user_not_found"

    def __init__(self, user_id: int) -> None:
        super().__init__(f"User {user_id} does not exist.")


class AlreadyReported(DomainError):
    """Rule 6 counts people, so each user reports a recommendation once."""

    code = "already_reported"

    def __init__(self) -> None:
        super().__init__("You already reported this recommendation.")
