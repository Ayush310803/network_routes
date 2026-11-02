from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NodeName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class NodeCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"name": "ServerA"}})

    name: NodeName


class NodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class EdgeCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"source": "ServerA", "destination": "ServerB", "latency": 12.5}}
    )

    source: NodeName
    destination: NodeName
    latency: float = Field(gt=0)


class EdgeOut(BaseModel):
    id: int
    source: str
    destination: str
    latency: float


class RouteRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"source": "ServerA", "destination": "ServerD"}}
    )

    source: NodeName
    destination: NodeName


class RouteOut(BaseModel):
    total_latency: float
    path: list[str]


class RouteQueryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    destination: str
    total_latency: float
    path: list[str]
    created_at: datetime
