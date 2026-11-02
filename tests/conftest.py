import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base
from core.dependencies import get_db
from main import app

SAMPLE_EDGES = [
    ("A", "B", 12.5),
    ("B", "D", 10.9),
    ("A", "C", 5),
    ("C", "D", 30),
    ("B", "C", 10.1),
]


@pytest.fixture
def client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def sample_graph(client):
    for name in ("A", "B", "C", "D"):
        client.post("/nodes", json={"name": name})
    for source, destination, latency in SAMPLE_EDGES:
        client.post(
            "/edges", json={"source": source, "destination": destination, "latency": latency}
        )
    return client
