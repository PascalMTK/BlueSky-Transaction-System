import math


def _haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_neighbor_order(stops):
    """Greedy nearest-neighbor ordering of delivery stops for a single
    driver's day. `stops` is a list of (lat, lon, delivery_id) tuples,
    already filtered to geocoded-only entries, sorted by scheduled_at
    (the first item is the starting point — there's no configured
    depot/office coordinate in the data model). Returns the same tuples
    reordered with a 1-based `sequence` number attached. This is a
    straight-line suggestion, not turn-by-turn driving directions."""
    remaining = list(stops)
    if not remaining:
        return []

    ordered = [remaining.pop(0)]
    while remaining:
        last_lat, last_lon, _ = ordered[-1]
        nearest_i = min(
            range(len(remaining)),
            key=lambda i: _haversine_km(last_lat, last_lon, remaining[i][0], remaining[i][1]),
        )
        ordered.append(remaining.pop(nearest_i))

    return [
        {'lat': lat, 'lon': lon, 'delivery_id': delivery_id, 'sequence': i + 1}
        for i, (lat, lon, delivery_id) in enumerate(ordered)
    ]
