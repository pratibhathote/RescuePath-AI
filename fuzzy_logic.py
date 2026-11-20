
# RESCUEPATH AI
# STEP 5: FUZZY LOGIC PRIORITY CALCULATION

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# INPUT VARIABLES
severity = ctrl.Antecedent(np.arange(1, 11, 1), "severity")
people = ctrl.Antecedent(np.arange(0, 101, 1), "people")
waiting_time = ctrl.Antecedent(
    np.arange(0, 181, 1), "waiting_time"
)

# OUTPUT VARIABLE
priority = ctrl.Consequent(np.arange(0, 101, 1), "priority")


# SEVERITY MEMBERSHIP FUNCTIONS
severity["low"] = fuzz.trimf(severity.universe, [1, 1, 5])
severity["medium"] = fuzz.trimf(severity.universe, [3, 6, 9])
severity["high"] = fuzz.trimf(severity.universe, [7, 10, 10])

# PEOPLE MEMBERSHIP FUNCTIONS
people["few"] = fuzz.trimf(people.universe, [0, 0, 30])
people["moderate"] = fuzz.trimf(people.universe, [15, 50, 80])
people["many"] = fuzz.trimf(people.universe, [60, 100, 100])

# WAITING TIME MEMBERSHIP FUNCTIONS
waiting_time["short"] = fuzz.trimf(
    waiting_time.universe, [0, 0, 60]
)
waiting_time["medium"] = fuzz.trimf(
    waiting_time.universe, [30, 90, 150]
)
waiting_time["long"] = fuzz.trimf(
    waiting_time.universe, [120, 180, 180]
)

# PRIORITY MEMBERSHIP FUNCTIONS
priority["low"] = fuzz.trimf(priority.universe, [0, 0, 40])
priority["medium"] = fuzz.trimf(priority.universe, [25, 50, 75])
priority["high"] = fuzz.trimf(priority.universe, [60, 100, 100])


# FUZZY RULES
rules = [
    ctrl.Rule(severity["high"], priority["high"]),
    ctrl.Rule(people["many"], priority["high"]),
    ctrl.Rule(waiting_time["long"], priority["high"]),

    ctrl.Rule(
        severity["medium"] & people["moderate"],
        priority["medium"]
    ),
    ctrl.Rule(
        severity["medium"] & waiting_time["medium"],
        priority["medium"]
    ),
    ctrl.Rule(
        people["moderate"] & waiting_time["medium"],
        priority["medium"]
    ),

    ctrl.Rule(
        severity["low"] & people["few"] & waiting_time["short"],
        priority["low"]
    ),
    ctrl.Rule(
        severity["low"] & people["few"],
        priority["low"]
    ),
    ctrl.Rule(
        severity["low"] & waiting_time["short"],
        priority["low"]
    )
]

priority_control = ctrl.ControlSystem(rules)


def calculate_priority(emergency):

    simulation = ctrl.ControlSystemSimulation(priority_control)

    simulation.input["severity"] = emergency["severity"]
    simulation.input["people"] = emergency["people_affected"]
    simulation.input["waiting_time"] = emergency["waiting_time"]

    simulation.compute()

    # Return fuzzy output when available
    if "priority" in simulation.output:
        return round(simulation.output["priority"], 2)

    # Fallback for input combinations not covered by fuzzy rules
    severity_score = (emergency["severity"] / 10) * 100
    people_score = min(emergency["people_affected"], 100)
    waiting_score = (
        min(emergency["waiting_time"], 180) / 180
    ) * 100

    fallback_score = (
        0.50 * severity_score
        + 0.25 * people_score
        + 0.25 * waiting_score
    )

    return round(fallback_score, 2)


def test_fuzzy_logic():

    from emergencies import emergencies

    print("\n================================")
    print("      FUZZY PRIORITY REPORT")
    print("================================")

    for emergency in emergencies:

        score = calculate_priority(emergency)

        print(
            emergency["id"],
            "|",
            emergency["type"],
            "| Priority:",
            score
        )

    print("\nAll emergency priorities calculated successfully!")


if __name__ == "__main__":
    test_fuzzy_logic()
