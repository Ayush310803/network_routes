import heapq
from collections import defaultdict


def find_shortest_path(
    edges: list[tuple[str, str, float]], source: str, destination: str
) -> tuple[float, list[str]] | None:
    """Dijkstra over directed, positively weighted edges.

    Returns (total_latency, path) or None when destination is unreachable from source.
    """
    if source == destination:
        return 0.0, [source]

    adjacency: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for edge_source, edge_destination, latency in edges:
        adjacency[edge_source].append((edge_destination, latency))

    dist = {source: 0.0}
    prev: dict[str, str] = {}
    heap = [(0.0, source)]

    while heap:
        current_dist, node = heapq.heappop(heap)
        if current_dist > dist[node]:
            continue
        if node == destination:
            break
        for neighbor, latency in adjacency[node]:
            candidate = current_dist + latency
            if candidate < dist.get(neighbor, float("inf")):
                dist[neighbor] = candidate
                prev[neighbor] = node
                heapq.heappush(heap, (candidate, neighbor))

    if destination not in dist:
        return None

    path = [destination]
    while path[-1] != source:
        path.append(prev[path[-1]])
    path.reverse()
    return dist[destination], path
