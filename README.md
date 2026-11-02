# Network Route Optimization API

A small REST service that stores servers (nodes) and latency links between them (edges), finds the lowest-latency route between two servers, and keeps a history of route lookups.

## How to run

With Docker (Postgres 16 + the API on port 8000):

```
docker compose up --build
```

The API container runs `alembic upgrade head` before starting uvicorn. Interactive docs are at http://localhost:8000/docs.

Without Docker, the app falls back to a local SQLite file (`routes.db`) when `DATABASE_URL` isn't set:

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

To point it at another database, copy `.env.example` to `.env` and set `DATABASE_URL`.

## How to run tests

```
pytest
pytest --cov=app --cov=core --cov=main --cov-report=term-missing
```

Tests use a fresh SQLite database per test, so they don't need Docker or Postgres.

## API

| Method | Path | Success | Errors |
|---|---|---|---|
| POST | `/nodes` | 201 `{id, name}` | 400 blank/missing name, duplicate |
| GET | `/nodes` | 200 list ordered by id | |
| DELETE | `/nodes/{id}` | 204 | 404 `NODE_NOT_FOUND` |
| POST | `/edges` | 201 `{id, source, destination, latency}` | 400 missing fields, latency <= 0, self-loop, unknown node, duplicate |
| GET | `/edges` | 200 list ordered by id | |
| DELETE | `/edges/{id}` | 204 | 404 `EDGE_NOT_FOUND` |
| POST | `/routes/shortest` | 200 `{total_latency, path}` | 400 missing fields or unknown node, 404 `NO_PATH` |
| GET | `/routes/history` | 200 list, newest first | 400 bad params or `date_from > date_to` |

`GET /health` also checks the database with `SELECT 1`.

`/routes/history` accepts `source`, `destination`, `date_from`, `date_to` (ISO 8601), `limit` (1-500, default 50) and `offset` (default 0). All are optional.

Every error has the same shape:

```json
{ "error": "Node 'ServerA' already exists", "code": "DUPLICATE_NODE" }
```

Walkthrough that builds the sample graph and queries A to D:

```
curl -X POST localhost:8000/nodes -H "Content-Type: application/json" -d '{"name": "A"}'
curl -X POST localhost:8000/nodes -H "Content-Type: application/json" -d '{"name": "B"}'
curl -X POST localhost:8000/nodes -H "Content-Type: application/json" -d '{"name": "C"}'
curl -X POST localhost:8000/nodes -H "Content-Type: application/json" -d '{"name": "D"}'

curl -X POST localhost:8000/edges -H "Content-Type: application/json" -d '{"source": "A", "destination": "B", "latency": 12.5}'
curl -X POST localhost:8000/edges -H "Content-Type: application/json" -d '{"source": "B", "destination": "D", "latency": 10.9}'
curl -X POST localhost:8000/edges -H "Content-Type: application/json" -d '{"source": "A", "destination": "C", "latency": 5}'
curl -X POST localhost:8000/edges -H "Content-Type: application/json" -d '{"source": "C", "destination": "D", "latency": 30}'
curl -X POST localhost:8000/edges -H "Content-Type: application/json" -d '{"source": "B", "destination": "C", "latency": 10.1}'

curl -X POST localhost:8000/routes/shortest -H "Content-Type: application/json" -d '{"source": "A", "destination": "D"}'
# {"total_latency":23.4,"path":["A","B","D"]}

curl -X POST localhost:8000/routes/shortest -H "Content-Type: application/json" -d '{"source": "D", "destination": "A"}'
# 404 {"error":"No path exists between D and A","code":"NO_PATH"}

curl "localhost:8000/routes/history?source=A&limit=10"
```

## Assumptions

The spec doesn't cover these, so I picked:

1. Edges are directed. A to B doesn't imply B to A, because network latency isn't always symmetric. Add two edges to link both ways.
2. Node names are trimmed and case-sensitive. A name that's empty after trimming counts as missing. Max length is 100.
3. Self-loop edges (source == destination) are rejected with 400.
4. A shortest-route query from a node to itself returns 200 with `path: [source]` and `total_latency: 0`.
5. Unknown nodes in `/routes/shortest` return 400, as the spec says. 404 means both nodes exist but no path connects them.
6. History only stores successful lookups. A failed lookup isn't a route.
7. Deleting a node deletes its incoming and outgoing edges. Route history is kept, since it stores names rather than foreign keys.
8. Latency is a float greater than 0. `total_latency` is rounded to 3 decimal places to hide float noise like `23.400000000000002`.
9. Validation errors return 400 instead of FastAPI's default 422, because the spec lists 400 for missing fields.

## Design notes

I used Dijkstra with a binary heap. All latencies are positive, so Dijkstra is correct. BFS would ignore the weights, and Bellman-Ford only pays off with negative edges. It runs in O((V + E) log V) and stops as soon as the destination is popped from the heap. The algorithm lives in `app/services/graph.py` with no database or FastAPI imports, so it's tested on its own.

Duplicate nodes and edges are caught by unique constraints in the database. I insert and catch the `IntegrityError` instead of checking with a SELECT first, because two concurrent requests could both pass the SELECT. Self-loops and non-positive latency are also enforced with CHECK constraints, not only in the request schema.

Route history stores source, destination and path as plain names rather than foreign keys. A history entry records what was answered at that point in time, so it should survive the nodes being deleted or the graph changing afterwards.

Each shortest-route request loads all edges in one joined query and builds the adjacency list in memory. That's fine at the scale of this assignment.

## What I'd change at scale

- Cache the adjacency list in memory or Redis and invalidate it on node and edge writes, instead of reading the whole edge table per request.
- Switch history to cursor pagination on `(created_at, id)`, since large offsets get slow.
- Partition history by month, or archive old rows, once the table grows.
- Precompute or cache hot source/destination pairs if the read pattern justified it.
