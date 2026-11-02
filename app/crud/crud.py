from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.model import Edge, Node, RouteQuery
from core.exceptions import ApiError
from core.logger import logger


def create_node(db: Session, name: str) -> Node:
    node = Node(name=name)
    db.add(node)
    # Insert first and let the unique constraint reject duplicates; a SELECT beforehand would race.
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ApiError(400, f"Node '{name}' already exists", "DUPLICATE_NODE")
    logger.info("Created node %s", name)
    return node


def get_node_by_name(db: Session, name: str) -> Node:
    node = db.scalar(select(Node).where(Node.name == name))
    if node is None:
        raise ApiError(400, f"Node '{name}' not found", "NODE_NOT_FOUND")
    return node


def list_nodes(db: Session) -> list[Node]:
    return list(db.scalars(select(Node).order_by(Node.id)))


def delete_node(db: Session, node_id: int) -> None:
    node = db.get(Node, node_id)
    if node is None:
        raise ApiError(404, f"Node with id {node_id} not found", "NODE_NOT_FOUND")
    # Edges are removed by ON DELETE CASCADE; history stores names, so it is kept.
    db.delete(node)
    db.commit()
    logger.info("Deleted node %s", node.name)


def create_edge(db: Session, source: str, destination: str, latency: float) -> Edge:
    if source == destination:
        raise ApiError(400, "source and destination must be different nodes", "VALIDATION_ERROR")
    edge = Edge(
        source=get_node_by_name(db, source),
        destination=get_node_by_name(db, destination),
        latency=latency,
    )
    db.add(edge)
    # Same as nodes: the unique constraint catches duplicates without a race.
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ApiError(400, f"Edge from '{source}' to '{destination}' already exists", "DUPLICATE_EDGE")
    logger.info("Created edge %s -> %s", source, destination)
    return edge


def list_edges(db: Session) -> list[Edge]:
    return list(db.scalars(select(Edge).order_by(Edge.id)))


def delete_edge(db: Session, edge_id: int) -> None:
    edge = db.get(Edge, edge_id)
    if edge is None:
        raise ApiError(404, f"Edge with id {edge_id} not found", "EDGE_NOT_FOUND")
    db.delete(edge)
    db.commit()
    logger.info("Deleted edge %s", edge_id)


def create_route_query(
    db: Session, source: str, destination: str, total_latency: float, path: list[str]
) -> None:
    db.add(RouteQuery(source=source, destination=destination, total_latency=total_latency, path=path))
    db.commit()


def to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def list_route_queries(
    db: Session,
    source: str | None,
    destination: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
    limit: int,
    offset: int,
) -> list[RouteQuery]:
    query = select(RouteQuery)
    if source:
        query = query.where(RouteQuery.source == source)
    if destination:
        query = query.where(RouteQuery.destination == destination)
    if date_from:
        query = query.where(RouteQuery.created_at >= to_utc(date_from))
    if date_to:
        query = query.where(RouteQuery.created_at <= to_utc(date_to))
    query = query.order_by(RouteQuery.created_at.desc(), RouteQuery.id.desc())
    return list(db.scalars(query.limit(limit).offset(offset)))
