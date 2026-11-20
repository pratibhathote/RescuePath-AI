
# RESCUEPATH AI
# STEP 9: MAIN SIMULATION ENGINE

from emergencies import emergencies
from fuzzy_logic import calculate_priority
from team_assignment import assign_team
from pathfinding import bfs, dfs, astar


def run_simulation():

    print("\n======================================")
    print("       RESCUEPATH AI SIMULATION")
    print("======================================")

    # Sort emergencies by priority
    emergency_results = []

    for emergency in emergencies:

        score = calculate_priority(emergency)

        emergency["priority"] = score

        emergency_results.append(emergency)

    emergency_results.sort(
        key=lambda e: e["priority"],
        reverse=True
    )

    print("\nTotal Emergencies:", len(emergency_results))

    print("\nProcessing Top 10 Priority Emergencies...")

    for emergency in emergency_results[:10]:

        print("\n--------------------------------------")
        print("Emergency ID:", emergency["id"])
        print("Disaster Type:", emergency["type"])
        print("Location:", emergency["location_name"])
        print("Coordinates:", emergency["location"])
        print("People Affected:", emergency["people_affected"])
        print("Severity:", emergency["severity"])
        print("Waiting Time:", emergency["waiting_time"])
        print("Priority Score:", emergency["priority"])

        # Assign rescue team
        assignment = assign_team(emergency)

        start = assignment["team_location"]
        goal = assignment["emergency_location"]

        print("\nAssigned Team:", assignment["team_name"])
        print("Team Starting Location:", start)

        # Calculate routes
        bfs_path = bfs(start, goal)
        dfs_path = dfs(start, goal)
        astar_path = astar(start, goal)

        print("\nBFS Route:", bfs_path)
        print("DFS Route:", dfs_path)
        print("A* Route:", astar_path)

        if astar_path:
            print("\nRescue Status: Route Available")
        else:
            print("\nRescue Status: No Route Available")

    print("\n======================================")
    print("       SIMULATION COMPLETED")
    print("======================================")


if __name__ == "__main__":
    run_simulation()
