
# RESCUEPATH AI
# STEP 7: PATHFINDING ALGORITHMS

import heapq

from city import (
    GRID_SIZE,
    BLOCKED_CELLS,
    RISK_MAP
)


# Get valid neighbouring cells
def get_neighbors(position):

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
            and new_position not in BLOCKED_CELLS
        ):
            neighbors.append(new_position)

    return neighbors


# BFS ALGORITHM
def bfs(start, goal):

    queue = [(start, [start])]
    visited = {start}

    while queue:

        current, path = queue.pop(0)

        if current == goal:
            return path

        for neighbor in get_neighbors(current):

            if neighbor not in visited:

                visited.add(neighbor)

                queue.append(
                    (neighbor, path + [neighbor])
                )

    return None


# DFS ALGORITHM
def dfs(start, goal):

    stack = [(start, [start])]
    visited = {start}

    while stack:

        current, path = stack.pop()

        if current == goal:
            return path

        for neighbor in get_neighbors(current):

            if neighbor not in visited:

                visited.add(neighbor)

                stack.append(
                    (neighbor, path + [neighbor])
                )

    return None


# MANHATTAN DISTANCE FOR A*
def heuristic(position, goal):

    return (
        abs(position[0] - goal[0])
        + abs(position[1] - goal[1])
    )


# A* ALGORITHM
def astar(start, goal):

    priority_queue = []

    heapq.heappush(
        priority_queue,
        (0, start)
    )

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

        for neighbor in get_neighbors(current):

            road_cost = 1 + RISK_MAP.get(neighbor, 0)

            new_cost = cost_so_far[current] + road_cost

            if (
                neighbor not in cost_so_far
                or new_cost < cost_so_far[neighbor]
            ):

                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current

                priority_value = (
                    new_cost + heuristic(neighbor, goal)
                )

                heapq.heappush(
                    priority_queue,
                    (priority_value, neighbor)
                )

    return None


# TEST ALL THREE ALGORITHMS
def test_pathfinding():

    start = (0, 7)
    goal = (7, 0)

    print("\n================================")
    print("       PATHFINDING REPORT")
    print("================================")

    print("\nStarting Point:", start)
    print("Destination:", goal)

    print("\nBFS Path:")
    print(bfs(start, goal))

    print("\nDFS Path:")
    print(dfs(start, goal))

    print("\nA* Path:")
    print(astar(start, goal))


if __name__ == "__main__":
    test_pathfinding()
