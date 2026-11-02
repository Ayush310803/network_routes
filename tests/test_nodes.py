def test_create_node(client):
    response = client.post("/nodes", json={"name": "ServerA"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "ServerA"
    assert isinstance(body["id"], int)


def test_create_duplicate_node(client):
    client.post("/nodes", json={"name": "ServerA"})
    response = client.post("/nodes", json={"name": "ServerA"})
    assert response.status_code == 400
    assert response.json() == {"error": "Node 'ServerA' already exists", "code": "DUPLICATE_NODE"}


def test_node_names_are_case_sensitive(client):
    client.post("/nodes", json={"name": "ServerA"})
    response = client.post("/nodes", json={"name": "servera"})
    assert response.status_code == 201


def test_create_node_blank_name(client):
    response = client.post("/nodes", json={"name": "   "})
    assert response.status_code == 400
    assert response.json() == {"error": "name: String should have at least 1 character", "code": "VALIDATION_ERROR"}


def test_create_node_missing_name(client):
    response = client.post("/nodes", json={})
    assert response.status_code == 400
    assert response.json() == {"error": "name: Field required", "code": "VALIDATION_ERROR"}


def test_create_node_without_body(client):
    response = client.post("/nodes")
    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_create_node_name_too_long(client):
    response = client.post("/nodes", json={"name": "x" * 101})
    assert response.status_code == 400
    assert response.json()["error"] == "name: String should have at most 100 characters"


def test_create_node_trims_name(client):
    response = client.post("/nodes", json={"name": "  ServerA  "})
    assert response.status_code == 201
    assert response.json()["name"] == "ServerA"

    duplicate = client.post("/nodes", json={"name": "ServerA"})
    assert duplicate.status_code == 400


def test_unknown_route_uses_error_shape(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert set(response.json()) == {"error", "code"}


def test_list_nodes(client):
    assert client.get("/nodes").json() == []
    client.post("/nodes", json={"name": "ServerB"})
    client.post("/nodes", json={"name": "ServerA"})

    response = client.get("/nodes")
    assert response.status_code == 200
    assert [node["name"] for node in response.json()] == ["ServerB", "ServerA"]


def test_delete_node_removes_its_edges(sample_graph):
    shortest = sample_graph.post("/routes/shortest", json={"source": "A", "destination": "D"})
    assert shortest.status_code == 200
    node_b = next(node for node in sample_graph.get("/nodes").json() if node["name"] == "B")

    response = sample_graph.delete(f"/nodes/{node_b['id']}")
    assert response.status_code == 204
    assert response.content == b""

    names = [node["name"] for node in sample_graph.get("/nodes").json()]
    assert names == ["A", "C", "D"]
    remaining = {(e["source"], e["destination"]) for e in sample_graph.get("/edges").json()}
    assert remaining == {("A", "C"), ("C", "D")}

    rerouted = sample_graph.post("/routes/shortest", json={"source": "A", "destination": "D"})
    assert rerouted.json() == {"total_latency": 35, "path": ["A", "C", "D"]}

    history = sample_graph.get("/routes/history").json()
    assert [entry["path"] for entry in history] == [["A", "C", "D"], ["A", "B", "D"]]


def test_delete_missing_node(client):
    response = client.delete("/nodes/999")
    assert response.status_code == 404
    assert response.json() == {"error": "Node with id 999 not found", "code": "NODE_NOT_FOUND"}


def test_delete_node_with_non_integer_id(client):
    response = client.delete("/nodes/abc")
    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
