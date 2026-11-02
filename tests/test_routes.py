from datetime import datetime, timedelta, timezone


def shortest(client, source, destination):
    return client.post("/routes/shortest", json={"source": source, "destination": destination})


def test_shortest_route_on_sample_graph(sample_graph):
    response = shortest(sample_graph, "A", "D")
    assert response.status_code == 200
    assert response.json() == {"total_latency": 23.4, "path": ["A", "B", "D"]}


def test_shortest_route_to_self(sample_graph):
    response = shortest(sample_graph, "A", "A")
    assert response.status_code == 200
    assert response.json() == {"total_latency": 0, "path": ["A"]}


def test_no_path_returns_404(sample_graph):
    response = shortest(sample_graph, "D", "A")
    assert response.status_code == 404
    assert response.json() == {"error": "No path exists between D and A", "code": "NO_PATH"}


def test_unknown_node_returns_400(sample_graph):
    response = shortest(sample_graph, "A", "Z")
    assert response.status_code == 400
    assert response.json() == {"error": "Node 'Z' not found", "code": "NODE_NOT_FOUND"}


def test_missing_field_returns_400(sample_graph):
    response = sample_graph.post("/routes/shortest", json={"source": "A"})
    assert response.status_code == 400
    assert response.json()["error"] == "destination: Field required"


def test_successful_query_is_saved_to_history(sample_graph):
    shortest(sample_graph, "A", "D")
    shortest(sample_graph, "D", "A")

    history = sample_graph.get("/routes/history").json()
    assert len(history) == 1
    entry = history[0]
    assert entry["source"] == "A"
    assert entry["destination"] == "D"
    assert entry["total_latency"] == 23.4
    assert entry["path"] == ["A", "B", "D"]
    assert "created_at" in entry


def test_history_is_newest_first(sample_graph):
    for destination in ("B", "C", "D"):
        shortest(sample_graph, "A", destination)

    history = sample_graph.get("/routes/history").json()
    assert [entry["destination"] for entry in history] == ["D", "C", "B"]


def test_history_filters_by_source_and_destination(sample_graph):
    shortest(sample_graph, "A", "D")
    shortest(sample_graph, "B", "D")
    shortest(sample_graph, "A", "C")

    by_source = sample_graph.get("/routes/history", params={"source": "A"}).json()
    assert {entry["destination"] for entry in by_source} == {"C", "D"}

    by_destination = sample_graph.get("/routes/history", params={"destination": "D"}).json()
    assert {entry["source"] for entry in by_destination} == {"A", "B"}

    both = sample_graph.get("/routes/history", params={"source": "A", "destination": "D"}).json()
    assert len(both) == 1


def test_history_limit_and_offset(sample_graph):
    for destination in ("B", "C", "D"):
        shortest(sample_graph, "A", destination)

    first_page = sample_graph.get("/routes/history", params={"limit": 2}).json()
    assert [entry["destination"] for entry in first_page] == ["D", "C"]

    second_page = sample_graph.get("/routes/history", params={"limit": 2, "offset": 2}).json()
    assert [entry["destination"] for entry in second_page] == ["B"]


def test_history_rejects_bad_limit(client):
    assert client.get("/routes/history", params={"limit": 0}).status_code == 400
    response = client.get("/routes/history", params={"limit": 501})
    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_history_date_range(sample_graph):
    shortest(sample_graph, "A", "D")
    now = datetime.now(timezone.utc)
    hour = timedelta(hours=1)

    def count(**params):
        params = {key: value.isoformat() for key, value in params.items()}
        return len(sample_graph.get("/routes/history", params=params).json())

    assert count(date_from=now - hour) == 1
    assert count(date_from=now + hour) == 0
    assert count(date_to=now - hour) == 0
    assert count(date_from=now - hour, date_to=now + hour) == 1


def test_history_date_range_with_other_timezone(sample_graph):
    shortest(sample_graph, "A", "D")
    ist = timezone(timedelta(hours=5, minutes=30))
    date_from = (datetime.now(timezone.utc) - timedelta(minutes=5)).astimezone(ist)

    history = sample_graph.get("/routes/history", params={"date_from": date_from.isoformat()})
    assert len(history.json()) == 1


def test_history_date_from_after_date_to(client):
    now = datetime.now(timezone.utc)
    response = client.get(
        "/routes/history",
        params={"date_from": now.isoformat(), "date_to": (now - timedelta(days=1)).isoformat()},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_DATE_RANGE"


def test_history_rejects_bad_date(client):
    response = client.get("/routes/history", params={"date_from": "yesterday"})
    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
