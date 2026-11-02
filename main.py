from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.routers import edges, nodes, routes
from core.dependencies import get_db
from core.exceptions import register_exception_handlers

app = FastAPI(title="Network Route Optimization API")
register_exception_handlers(app)
app.include_router(nodes.router)
app.include_router(edges.router)
app.include_router(routes.router)


@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
