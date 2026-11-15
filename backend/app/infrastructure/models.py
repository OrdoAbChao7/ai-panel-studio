"""SQLAlchemy 2 ORM Models for Persistence."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.infrastructure.database import Base


class DiscussionModel(Base):
    """SQLAlchemy model for discussions table."""

    __tablename__ = "discussions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="created", index=True)
    current_round = Column(Integer, nullable=False, default=0)
    max_rounds = Column(Integer, nullable=False, default=5)
    summary = Column(Text, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    participants = relationship(
        "ParticipantModel", back_populates="discussion", cascade="all, delete-orphan"
    )
    turns = relationship(
        "TurnModel", back_populates="discussion", cascade="all, delete-orphan"
    )
    events = relationship(
        "EventModel", back_populates="discussion", cascade="all, delete-orphan"
    )
    consensus_items = relationship(
        "ConsensusItemModel", back_populates="discussion", cascade="all, delete-orphan"
    )
    divergence_items = relationship(
        "DivergenceItemModel", back_populates="discussion", cascade="all, delete-orphan"
    )


class ParticipantModel(Base):
    """SQLAlchemy model for participants table."""

    __tablename__ = "participants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    discussion_id = Column(
        String(36),
        ForeignKey("discussions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=False)
    occupation = Column(String(100), nullable=False)
    stance = Column(Text, nullable=False)
    perspective = Column(Text, nullable=False)
    color_hex = Column(String(10), nullable=False)
    role = Column(String(20), nullable=False, default="expert")
    total_turns_spoken = Column(Integer, nullable=False, default=0)
    last_spoken_turn = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    discussion = relationship("DiscussionModel", back_populates="participants")


class TurnModel(Base):
    """SQLAlchemy model for turns table."""

    __tablename__ = "turns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    discussion_id = Column(
        String(36),
        ForeignKey("discussions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_number = Column(Integer, nullable=False)
    round_number = Column(Integer, nullable=False)
    speaker_id = Column(String(36), ForeignKey("participants.id"), nullable=False, index=True)
    speaker_name = Column(String(100), nullable=False)
    action_type = Column(String(30), nullable=False)
    content = Column(Text, nullable=False)
    rationale = Column(Text, nullable=True)
    priority_score = Column(Float, nullable=False, default=0.0)
    target_speaker_id = Column(String(36), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    discussion = relationship("DiscussionModel", back_populates="turns")


class EventModel(Base):
    """SQLAlchemy model for events table."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discussion_id = Column(
        String(36),
        ForeignKey("discussions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seq_id = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)
    payload = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    discussion = relationship("DiscussionModel", back_populates="events")


class ConsensusItemModel(Base):
    """SQLAlchemy model for consensus_items table."""

    __tablename__ = "consensus_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    discussion_id = Column(
        String(36),
        ForeignKey("discussions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    statement = Column(Text, nullable=False)
    supporting_agents = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    resolved_turn = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    discussion = relationship("DiscussionModel", back_populates="consensus_items")


class DivergenceItemModel(Base):
    """SQLAlchemy model for divergence_items table."""

    __tablename__ = "divergence_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    discussion_id = Column(
        String(36),
        ForeignKey("discussions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tension = Column(Text, nullable=False)
    opposing_stances = Column(Text, nullable=False)
    intensity = Column(Float, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    discussion = relationship("DiscussionModel", back_populates="divergence_items")
