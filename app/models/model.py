from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )


class Edge(Base):
    __tablename__ = "edges"
    __table_args__ = (
        UniqueConstraint("source_id", "destination_id", name="uq_edges_source_destination"),
        CheckConstraint("source_id != destination_id", name="ck_edges_no_self_loop"),
        CheckConstraint("latency > 0", name="ck_edges_latency_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    latency: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )

    source: Mapped[Node] = relationship(foreign_keys=[source_id], lazy="joined")
    destination: Mapped[Node] = relationship(foreign_keys=[destination_id], lazy="joined")


class RouteQuery(Base):
    __tablename__ = "route_queries"
    __table_args__ = (
        Index("ix_route_queries_source_destination_created_at", "source", "destination", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    destination: Mapped[str] = mapped_column(String(100), nullable=False)
    total_latency: Mapped[float] = mapped_column(Float, nullable=False)
    path: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False, index=True
    )
