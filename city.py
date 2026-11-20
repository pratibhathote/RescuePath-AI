
# RESCUEPATH AI
# STEP 2: CITY CONFIGURATION

GRID_SIZE = 8

HOSPITAL = (0, 0)
SHELTER = (7, 7)

RESCUE_TEAMS = {
    "Flood Rescue Team": (0, 7),
    "Medical Team": (7, 0),
    "Fire Rescue Team": (1, 3),
    "General Rescue Team": (6, 4)
}

BLOCKED_CELLS = {
    (3, 3),
    (4, 4)
}

RISK_MAP = {
    (2, 3): 2,
    (2, 4): 3,
    (3, 4): 2,
    (5, 3): 3,
    (5, 4): 2
}


def create_city():

    city = []

    for row in range(GRID_SIZE):

        current_row = []

        for col in range(GRID_SIZE):

            position = (row, col)

            if position == HOSPITAL:
                symbol = "H"

            elif position == SHELTER:
                symbol = "S"

            elif position in BLOCKED_CELLS:
                symbol = "X"

            elif position in RESCUE_TEAMS.values():
                symbol = "R"

            else:
                symbol = "."

            current_row.append(symbol)

        city.append(current_row)

    return city


def display_city():

    city = create_city()

    print("\n========== RESCUEPATH AI ==========\n")

    for row in city:
        print(" ".join(row))

    print("\nH = Hospital")
    print("S = Shelter")
    print("R = Rescue Team")
    print("X = Blocked Road")
    print(". = Normal Road")


if __name__ == "__main__":
    display_city()
