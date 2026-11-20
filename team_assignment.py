# RESCUEPATH AI
# STEP 6: RESCUE TEAM ASSIGNMENT

from city import RESCUE_TEAMS


# Disaster-specific team mapping
TEAM_MAPPING = {
    "Flood": "Flood Rescue Team",
    "Storm": "Flood Rescue Team",
    "Accident": "Medical Team",
    "Fire": "Fire Rescue Team",
    "Earthquake": "General Rescue Team",
    "Landslide": "General Rescue Team"
}


def assign_team(emergency):

    disaster_type = emergency["type"]

    # Select suitable team
    team_name = TEAM_MAPPING.get(
        disaster_type,
        "General Rescue Team"
    )

    # Get team's starting location
    team_location = RESCUE_TEAMS[team_name]

    return {
        "team_name": team_name,
        "team_location": team_location,
        "emergency_location": emergency["location"],
        "priority": emergency.get("priority", 0)
    }


def test_team_assignment():

    from emergencies import emergencies
    from fuzzy_logic import calculate_priority

    print("\n================================")
    print("       RESCUE TEAM ASSIGNMENT")
    print("================================")

    for emergency in emergencies[:10]:

        score = calculate_priority(emergency)
        emergency["priority"] = score

        assignment = assign_team(emergency)

        print("\nEmergency:", emergency["id"])
        print("Disaster:", emergency["type"])
        print("Priority:", score)
        print("Assigned Team:", assignment["team_name"])
        print("Team Location:", assignment["team_location"])
        print("Emergency Location:", assignment["emergency_location"])
        print("--------------------------------")


if __name__ == "__main__":
    test_team_assignment()