from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.crud import crud
from app.models.model import Edge
from app.schemas.schema import EdgeCreate, EdgeOut
from core.dependencies import get_db

router = APIRouter(prefix="/edges", tags=["edges"])


def to_edge_out(edge: Edge) -> EdgeOut:
    return EdgeOut(
        id=edge.id,
        source=edge.source.name,
        destination=edge.destination.name,
        latency=edge.latency,
    )


@router.post("", response_model=EdgeOut, status_code=status.HTTP_201_CREATED)
def create_edge(payload: EdgeCreate, db: Session = Depends(get_db)):
    edge = crud.create_edge(db, payload.source, payload.destination, payload.latency)
    return to_edge_out(edge)


@router.get("", response_model=list[EdgeOut], status_code=status.HTTP_200_OK)
def list_edges(db: Session = Depends(get_db)):
    return [to_edge_out(edge) for edge in crud.list_edges(db)]


@router.delete("/{edge_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_edge(edge_id: int, db: Session = Depends(get_db)):
    crud.delete_edge(db, edge_id)
