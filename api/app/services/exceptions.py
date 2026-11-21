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
