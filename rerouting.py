
# RESCUEPATH AI
# STEP 8: DYNAMIC ROUTE REROUTING

from city import BLOCKED_CELLS, GRID_SIZE
from pathfinding import astar, get_neighbors


# Create a temporary blocked-road set
def find_alternative_route(start, goal, blocked_road):

    temporary_blocked = set(BLOCKED_CELLS)
    temporary_blocked.add(blocked_road)

    def safe_neighbors(position):

        row, col = position

        directions = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1)
        ]

        neighbors = []

        for dr, dc in directions:

            new_row = row + dr
            new_col = col + dc

            new_position = (new_row, new_col)

            if (
                0 <= new_row < GRID_SIZE
                and 0 <= new_col < GRID_SIZE
                and new_position not in temporary_blocked
            ):
                neighbors.append(new_position)

        return neighbors

    import heapq
    from city import RISK_MAP

    priority_queue = [(0, start)]

    came_from = {start: None}
    cost_so_far = {start: 0}

    while priority_queue:

        _, current = heapq.heappop(priority_queue)

        if current == goal:

            path = []

            while current is not None:
                path.append(current)
                current = came_from[current]

            return path[::-1]

        for neighbor in safe_neighbors(current):

            road_cost = 1 + RISK_MAP.get(neighbor, 0)

            new_cost = cost_so_far[current] + road_cost

            if (
                neighbor not in cost_so_far
                or new_cost < cost_so_far[neighbor]
            ):

                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current

                heuristic = (
                    abs(neighbor[0] - goal[0])
                    + abs(neighbor[1] - goal[1])
                )

                priority = new_cost + heuristic

                heapq.heappush(
                    priority_queue,
                    (priority, neighbor)
                )

    return None


# TEST REROUTING
def test_rerouting():

    start = (0, 7)
    goal = (7, 0)

    original_path = astar(start, goal)

    print("\n================================")
    print("       ROUTE REROUTING")
    print("================================")

    print("\nOriginal Route:")
    print(original_path)

    if not original_path or len(original_path) < 3:
        print("No suitable route available for this test.")
        return

    # Block a cell on the original route
    blocked_road = original_path[len(original_path) // 2]

    print("\nRoad Blocked At:", blocked_road)

    alternative_path = find_alternative_route(
        start,
        goal,
        blocked_road
    )

    print("\nAlternative Route:")
    print(alternative_path)

    if alternative_path:
        print("\nRoute successfully recalculated!")
    else:
        print("\nNo alternative route available!")


if __name__ == "__main__":
    test_rerouting()
