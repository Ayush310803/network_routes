"""create nodes, edges and route_queries

Revision ID: 0001
Revises:
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "edges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("destination_id", sa.Integer(), sa.ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("latency", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_id", "destination_id", name="uq_edges_source_destination"),
        sa.CheckConstraint("source_id != destination_id", name="ck_edges_no_self_loop"),
        sa.CheckConstraint("latency > 0", name="ck_edges_latency_positive"),
    )
    op.create_table(
        "route_queries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("destination", sa.String(100), nullable=False),
        sa.Column("total_latency", sa.Float(), nullable=False),
        sa.Column("path", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_route_queries_created_at", "route_queries", ["created_at"])
    op.create_index(
        "ix_route_queries_source_destination_created_at",
        "route_queries",
        ["source", "destination", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_route_queries_source_destination_created_at", table_name="route_queries")
    op.drop_index("ix_route_queries_created_at", table_name="route_queries")
    op.drop_table("route_queries")
    op.drop_table("edges")
    op.drop_table("nodes")
