"""Domain Exceptions for AI Panel Studio."""


class DomainError(Exception):
    """Base exception for all domain layer business rule violations."""

    pass


class DomainStateError(DomainError):
    """Raised when an illegal lifecycle state transition or operation in invalid state is attempted."""

    pass


class DomainInvariantError(DomainError):
    """Raised when an aggregate invariant, consistency boundary, or business rule is violated."""

    pass
