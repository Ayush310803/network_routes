from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.crud import crud
from app.schemas.schema import NodeCreate, NodeOut
from core.dependencies import get_db

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.post("", response_model=NodeOut, status_code=status.HTTP_201_CREATED)
def create_node(payload: NodeCreate, db: Session = Depends(get_db)):
    return crud.create_node(db, payload.name)


@router.get("", response_model=list[NodeOut], status_code=status.HTTP_200_OK)
def list_nodes(db: Session = Depends(get_db)):
    return crud.list_nodes(db)


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_node(node_id: int, db: Session = Depends(get_db)):
    crud.delete_node(db, node_id)
