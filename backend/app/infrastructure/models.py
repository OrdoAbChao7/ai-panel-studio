"""SQLAlchemy 2.0 ORM Models for AI Panel Studio Persistence."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


class DiscussionModel(Base):
    """SQLAlchemy model for discussions table."""

    __tablename__ = "discussions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="created"
    )
    current_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    participants: Mapped[List["ParticipantModel"]] = relationship(
        "ParticipantModel",
        back_populates="discussion",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )
    turns: Mapped[List["TurnModel"]] = relationship(
        "TurnModel",
        back_populates="discussion",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        order_by="TurnModel.turn_number",
    )
    events: Mapped[List["EventModel"]] = relationship(
        "EventModel",
        back_populates="discussion",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        order_by="EventModel.seq_id",
    )
    consensus_items: Mapped[List["ConsensusItemModel"]] = relationship(
        "ConsensusItemModel",
        back_populates="discussion",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )
    divergence_items: Mapped[List["DivergenceItemModel"]] = relationship(
        "DivergenceItemModel",
        back_populates="discussion",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_discussions_status", "status"),
        Index("idx_discussions_created_at", created_at.desc()),
    )


class ParticipantModel(Base):
    """SQLAlchemy model for participants table."""

    __tablename__ = "participants"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    discussion_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("discussions.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    occupation: Mapped[str] = mapped_column(String(100), nullable=False)
    stance: Mapped[str] = mapped_column(Text, nullable=False)
    perspective: Mapped[str] = mapped_column(Text, nullable=False)
    color_hex: Mapped[str] = mapped_column(String(10), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="expert")
    total_turns_spoken: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_spoken_turn: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    discussion: Mapped["DiscussionModel"] = relationship(
        "DiscussionModel", back_populates="participants"
    )

    __table_args__ = (Index("idx_participants_discussion_id", "discussion_id"),)


class TurnModel(Base):
    """SQLAlchemy model for turns table."""

    __tablename__ = "turns"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    discussion_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("discussions.id", ondelete="CASCADE"),
        nullable=False,
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
    )
    speaker_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    target_speaker_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, default=None
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    discussion: Mapped["DiscussionModel"] = relationship(
        "DiscussionModel", back_populates="turns"
    )
    speaker: Mapped[Optional["ParticipantModel"]] = relationship("ParticipantModel")

    __table_args__ = (
        Index("idx_turns_discussion_turn", "discussion_id", "turn_number"),
        Index("idx_turns_speaker_id", "speaker_id"),
    )


class EventModel(Base):
    """SQLAlchemy model for events table."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    discussion_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("discussions.id", ondelete="CASCADE"),
        nullable=False,
    )
    seq_id: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    discussion: Mapped["DiscussionModel"] = relationship(
        "DiscussionModel", back_populates="events"
    )

    __table_args__ = (
        Index("idx_events_discussion_seq", "discussion_id", "seq_id", unique=True),
        Index("idx_events_discussion_id", "discussion_id"),
    )


class ConsensusItemModel(Base):
    """SQLAlchemy model for consensus_items table."""

    __tablename__ = "consensus_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    discussion_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("discussions.id", ondelete="CASCADE"),
        nullable=False,
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_agents: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    resolved_turn: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    discussion: Mapped["DiscussionModel"] = relationship(
        "DiscussionModel", back_populates="consensus_items"
    )

    __table_args__ = (Index("idx_consensus_discussion_id", "discussion_id"),)


class DivergenceItemModel(Base):
    """SQLAlchemy model for divergence_items table."""

    __tablename__ = "divergence_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    discussion_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("discussions.id", ondelete="CASCADE"),
        nullable=False,
    )
    tension: Mapped[str] = mapped_column(Text, nullable=False)
    opposing_stances: Mapped[str] = mapped_column(Text, nullable=False)  # JSON dict
    intensity: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    discussion: Mapped["DiscussionModel"] = relationship(
        "DiscussionModel", back_populates="divergence_items"
    )

    __table_args__ = (Index("idx_divergence_discussion_id", "discussion_id"),)
