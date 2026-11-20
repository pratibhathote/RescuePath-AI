
# RESCUEPATH AI
# STEP 4: EMERGENCY MANAGEMENT SYSTEM

from dataset_loader import load_dataset

# Load dataset emergencies
emergencies = load_dataset()


def display_emergencies():

    print("\n================================")
    print("       EMERGENCY REPORTS")
    print("================================")

    for emergency in emergencies:

        print("\nEmergency ID:", emergency["id"])
        print("Disaster Type:", emergency["type"])
        print("Location:", emergency["location_name"])
        print("Coordinates:", emergency["location"])
        print("People Affected:", emergency["people_affected"])
        print("Severity:", emergency["severity"], "/ 10")
        print("Waiting Time:", emergency["waiting_time"], "minutes")
        print("Road Condition:", emergency["road_condition"])
        print("Status:", emergency["status"])

        print("--------------------------------")


def add_emergency(
    emergency_id,
    disaster_type,
    location_name,
    row,
    col,
    people,
    severity,
    waiting_time,
    road_condition
):

    # Check duplicate ID
    if any(e["id"] == emergency_id for e in emergencies):
        print("Emergency ID already exists!")
        return

    # Validate location
    if not (0 <= row < 8 and 0 <= col < 8):
        print("Invalid location! Coordinates must be between 0 and 7.")
        return

    if not 1 <= severity <= 10:
        print("Severity must be between 1 and 10.")
        return

    if people < 1 or waiting_time < 0:
        print("Invalid people count or waiting time.")
        return

    road_condition = road_condition.lower()

    if road_condition not in ["safe", "risky", "blocked"]:
        print("Invalid road condition!")
        return

    new_emergency = {
        "id": emergency_id,
        "type": disaster_type,
        "location_name": location_name,
        "location": (row, col),
        "people_affected": people,
        "severity": severity,
        "waiting_time": waiting_time,
        "road_condition": road_condition,
        "record_origin": "manual_entry",
        "reference_source": "User entered",
        "source_url": "",
        "status": "Pending"
    }

    emergencies.append(new_emergency)

    print("\nNew emergency added successfully!")


if __name__ == "__main__":

    display_emergencies()

    print("\nTotal Emergency Requests:", len(emergencies))
