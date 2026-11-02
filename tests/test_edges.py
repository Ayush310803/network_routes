import pytest


@pytest.fixture
def two_nodes(client):
    client.post("/nodes", json={"name": "ServerA"})
    client.post("/nodes", json={"name": "ServerB"})
    return client


def post_edge(client, source="ServerA", destination="ServerB", latency=12.5):
    return client.post(
        "/edges", json={"source": source, "destination": destination, "latency": latency}
    )


def test_create_edge(two_nodes):
    response = post_edge(two_nodes)
    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "ServerA"
    assert body["destination"] == "ServerB"
    assert body["latency"] == 12.5
    assert isinstance(body["id"], int)


@pytest.mark.parametrize("latency", [0, -5])
def test_create_edge_non_positive_latency(two_nodes, latency):
    response = post_edge(two_nodes, latency=latency)
    assert response.status_code == 400
    assert response.json() == {
        "error": "latency: Input should be greater than 0",
        "code": "VALIDATION_ERROR",
    }


def test_create_edge_missing_fields(two_nodes):
    response = two_nodes.post("/edges", json={"source": "ServerA", "latency": 3})
    assert response.status_code == 400
    assert response.json()["error"] == "destination: Field required"


def test_create_edge_unknown_source(two_nodes):
    response = post_edge(two_nodes, source="ServerX")
    assert response.status_code == 400
    assert response.json() == {"error": "Node 'ServerX' not found", "code": "NODE_NOT_FOUND"}


def test_create_edge_unknown_destination(two_nodes):
    response = post_edge(two_nodes, destination="ServerY")
    assert response.status_code == 400
    assert response.json() == {"error": "Node 'ServerY' not found", "code": "NODE_NOT_FOUND"}


def test_create_edge_self_loop(two_nodes):
    response = post_edge(two_nodes, destination="ServerA")
    assert response.status_code == 400
    assert response.json() == {
        "error": "source and destination must be different nodes",
        "code": "VALIDATION_ERROR",
    }


def test_create_duplicate_edge(two_nodes):
    post_edge(two_nodes)
    response = post_edge(two_nodes, latency=99)
    assert response.status_code == 400
    assert response.json() == {
        "error": "Edge from 'ServerA' to 'ServerB' already exists",
        "code": "DUPLICATE_EDGE",
    }


def test_reverse_edge_is_allowed(two_nodes):
    post_edge(two_nodes)
    response = post_edge(two_nodes, source="ServerB", destination="ServerA", latency=14)
    assert response.status_code == 201


def test_list_edges(sample_graph):
    response = sample_graph.get("/edges")
    assert response.status_code == 200
    edges = [(e["source"], e["destination"], e["latency"]) for e in response.json()]
    assert edges == [
        ("A", "B", 12.5),
        ("B", "D", 10.9),
        ("A", "C", 5),
        ("C", "D", 30),
        ("B", "C", 10.1),
    ]


def test_delete_edge(two_nodes):
    edge_id = post_edge(two_nodes).json()["id"]

    response = two_nodes.delete(f"/edges/{edge_id}")
    assert response.status_code == 204
    assert two_nodes.get("/edges").json() == []

    recreated = post_edge(two_nodes)
    assert recreated.status_code == 201


def test_delete_missing_edge(client):
    response = client.delete("/edges/999")
    assert response.status_code == 404
    assert response.json() == {"error": "Edge with id 999 not found", "code": "EDGE_NOT_FOUND"}
