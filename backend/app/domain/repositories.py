"""Domain Repository Interfaces for Persistence Abstraction."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities import DiscussionAggregate
from app.domain.events import DomainEvent


class IDiscussionRepository(ABC):
    """Repository interface for persisting and reconstituting DiscussionAggregate."""

    @abstractmethod
    async def get_by_id(self, discussion_id: str) -> Optional[DiscussionAggregate]:
        """Fetch discussion aggregate by ID, reconstituting all child entities."""
        pass

    @abstractmethod
    async def save(self, discussion: DiscussionAggregate) -> None:
        """Persist or update discussion aggregate and all child entities atomically."""
        pass

    @abstractmethod
    async def list_all(self) -> List[DiscussionAggregate]:
        """List all discussion summaries/aggregates ordered by created_at descending."""
        pass

    @abstractmethod
    async def delete(self, discussion_id: str) -> bool:
        """Delete discussion session and all cascaded children by ID. Returns True if found and deleted."""
        pass


class IEventStreamRepository(ABC):
    """Repository interface for monotonic session event logging and SSE replay."""

    @abstractmethod
    async def append_event(self, discussion_id: str, event: DomainEvent) -> int:
        """Append domain event with next atomically allocated monotonic seq_id. Returns allocated seq_id."""
        pass

    @abstractmethod
    async def get_events_since(
        self, discussion_id: str, last_seq_id: int
    ) -> List[DomainEvent]:
        """Fetch all events for discussion with seq_id strictly greater than last_seq_id in monotonic ascending order."""
        pass
