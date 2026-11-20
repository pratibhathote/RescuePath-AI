
# RESCUEPATH AI
# STEP 3: DATASET LOADER

import csv
import os
from city import GRID_SIZE

DATASET_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "disaster_dataset.csv"
)


def load_dataset():

    if not os.path.exists(DATASET_FILE):
        raise FileNotFoundError(
            "disaster_dataset.csv not found in project folder!"
        )

    emergencies = []

    with open(
        DATASET_FILE,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        required_columns = [
            "emergency_id",
            "disaster_type",
            "location_name",
            "grid_row",
            "grid_col",
            "people_affected",
            "severity",
            "waiting_time_minutes",
            "road_condition",
            "record_origin",
            "reference_source",
            "source_url"
        ]

        if not reader.fieldnames:
            raise ValueError("Dataset is empty!")

        missing = [
            col for col in required_columns
            if col not in reader.fieldnames
        ]

        if missing:
            raise ValueError(f"Missing columns: {missing}")

        for row in reader:

            emergency = {
                "id": row["emergency_id"],
                "type": row["disaster_type"],
                "location_name": row["location_name"],
                "location": (
                    int(row["grid_row"]),
                    int(row["grid_col"])
                ),
                "people_affected": int(row["people_affected"]),
                "severity": int(row["severity"]),
                "waiting_time": int(
                    row["waiting_time_minutes"]
                ),
                "road_condition": row["road_condition"].lower(),
                "record_origin": row["record_origin"],
                "reference_source": row["reference_source"],
                "source_url": row["source_url"],
                "status": "Pending"
            }

            r, c = emergency["location"]

            if not (0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE):
                raise ValueError(
                    f"Invalid location for {emergency['id']}"
                )

            if not 1 <= emergency["severity"] <= 10:
                raise ValueError(
                    f"Invalid severity for {emergency['id']}"
                )

            if emergency["people_affected"] < 1:
                raise ValueError(
                    f"Invalid people count for {emergency['id']}"
                )

            if emergency["waiting_time"] < 0:
                raise ValueError(
                    f"Invalid waiting time for {emergency['id']}"
                )

            if emergency["road_condition"] not in [
                "safe", "risky", "blocked"
            ]:
                raise ValueError(
                    f"Invalid road condition for {emergency['id']}"
                )

            emergencies.append(emergency)

    ids = [e["id"] for e in emergencies]

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate emergency IDs found!")

    return emergencies


def display_dataset():

    emergencies = load_dataset()

    print("\n================================")
    print("       RESCUEPATH AI")
    print("       DATASET REPORT")
    print("================================")

    print("Total Records:", len(emergencies))

    categories = {}

    for emergency in emergencies:
        disaster = emergency["type"]
        categories[disaster] = categories.get(disaster, 0) + 1

    print("\nDisaster Categories:")

    for disaster, count in categories.items():
        print(disaster, ":", count)

    print("\nFirst 5 Records:")

    for emergency in emergencies[:5]:
        print(
            emergency["id"],
            "|", emergency["type"],
            "|", emergency["location"],
            "| Severity:", emergency["severity"]
        )

    print("\nDataset loaded and validated successfully!")


if __name__ == "__main__":
    display_dataset()
