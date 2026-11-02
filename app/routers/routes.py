from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.crud import crud
from app.schemas.schema import RouteOut, RouteQueryOut, RouteRequest
from app.services.graph import find_shortest_path
from core.dependencies import get_db
from core.exceptions import ApiError

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/shortest", response_model=RouteOut, status_code=status.HTTP_200_OK)
def shortest_route(payload: RouteRequest, db: Session = Depends(get_db)):
    crud.get_node_by_name(db, payload.source)
    crud.get_node_by_name(db, payload.destination)

    edges = [(e.source.name, e.destination.name, e.latency) for e in crud.list_edges(db)]
    result = find_shortest_path(edges, payload.source, payload.destination)
    if result is None:
        message = f"No path exists between {payload.source} and {payload.destination}"
        raise ApiError(404, message, "NO_PATH")

    total_latency = round(result[0], 3)
    path = result[1]
    crud.create_route_query(db, payload.source, payload.destination, total_latency, path)
    return RouteOut(total_latency=total_latency, path=path)


@router.get("/history", response_model=list[RouteQueryOut], status_code=status.HTTP_200_OK)
def route_history(
    source: str | None = None,
    destination: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    if date_from and date_to and crud.to_utc(date_from) > crud.to_utc(date_to):
        raise ApiError(400, "date_from must not be after date_to", "INVALID_DATE_RANGE")
    return crud.list_route_queries(db, source, destination, date_from, date_to, limit, offset)
