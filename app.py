
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import inspect
import heapq
import math
import random
from pathlib import Path
from collections import deque

# ============================================================
# RESCUEPATH AI — COMPLETE STREAMLIT APPLICATION
# ============================================================

st.set_page_config(
    page_title="RescuePath AI",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- PROJECT MODULES -----------------------

try:
    import city
except Exception:
    city = None

try:
    import fuzzy_logic
except Exception:
    fuzzy_logic = None

try:
    import team_assignment
except Exception:
    team_assignment = None

try:
    import pathfinding
except Exception:
    pathfinding = None

try:
    import rerouting
except Exception:
    rerouting = None

try:
    import simulation
except Exception:
    simulation = None

try:
    import emergencies as emergency_module
except Exception:
    emergency_module = None

# -------------------- CITY CONFIGURATION -------------------

def city_value(name, default):
    if city is not None:
        return getattr(city, name, default)
    return default

GRID_SIZE = city_value("GRID_SIZE", 8)
HOSPITAL = city_value("HOSPITAL", (0, 0))
SHELTER = city_value("SHELTER", (7, 7))
RESCUE_TEAMS = city_value("RESCUE_TEAMS", [])
BLOCKED_CELLS = city_value("BLOCKED_CELLS", [])
RISK_MAP = city_value("RISK_MAP", {})

try:
    GRID_SIZE = int(GRID_SIZE)
except Exception:
    GRID_SIZE = 8

GRID_SIZE = max(2, min(GRID_SIZE, 20))

# -------------------- DESIGN -------------------------------

st.markdown("""
<style>
.stApp {
    background: #071321;
    color: #eaf3ff;
}
[data-testid="stSidebar"] {
    background: #0b1c2d;
    border-right: 1px solid #1b3a54;
}
h1,h2,h3,h4 {
    color: #eaf5ff !important;
}
p, label, span {
    color: #c4d5e6;
}
[data-testid="stMetric"] {
    background: #10263b;
    border: 1px solid #1d4964;
    border-radius: 12px;
    padding: 15px;
}
[data-testid="stMetricValue"] {
    color: #35d5ed !important;
}
.stButton button {
    background: linear-gradient(90deg,#087da6,#12b9ce);
    color: white;
    border: 0;
    border-radius: 8px;
    font-weight: 600;
    min-height: 40px;
}
.stButton button:hover {
    background: #26cde1;
    color: #071321;
}
.stTabs [aria-selected="true"] {
    color: #35d5ed !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #0c2033;
    border: 1px solid #1b405a;
    border-radius: 12px;
}
hr {
    border-color: #1d3a52;
}
.small-muted {
    color: #829db5;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

# -------------------- SESSION STATE ------------------------

def init_state(key, value):
    if key not in st.session_state:
        st.session_state[key] = value

init_state("emergency_data", [])
init_state("blocked_cells", [])
init_state("selected_id", None)
init_state("active_route", [])
init_state("alternative_route", [])
init_state("route_algorithm", "A*")
init_state("assigned_teams", {})
init_state("simulation_running", False)
init_state("simulation_tick", 0)
init_state("event_log", [])
init_state("manual_emergency_counter", 0)

# -------------------- HELPERS ------------------------------

def coord(value, default=None):
    if isinstance(value, (tuple, list)) and len(value) >= 2:
        try:
            return int(value[0]), int(value[1])
        except Exception:
            return default

    if isinstance(value, dict):
        row = value.get("row", value.get("grid_row"))
        col = value.get("col", value.get("grid_col"))
        if row is not None and col is not None:
            return int(row), int(col)

    return default


def clamp_position(position):
    r, c = position
    return (
        max(0, min(GRID_SIZE - 1, int(r))),
        max(0, min(GRID_SIZE - 1, int(c)))
    )


def get_field(record, names, default=None):
    for name in names:
        if name in record and pd.notna(record[name]):
            return record[name]
    return default


def normalize_record(record):
    record = dict(record)

    result = {
        **record,
        "emergency_id": str(get_field(
            record, ["emergency_id", "id"], "EM-000"
        )),
        "disaster_type": str(get_field(
            record, ["disaster_type", "type"], "Unknown"
        )),
        "location_name": str(get_field(
            record, ["location_name", "location"], "Unknown"
        )),
        "grid_row": int(get_field(
            record, ["grid_row", "row"], 0
        )),
        "grid_col": int(get_field(
            record, ["grid_col", "col", "column"], 0
        )),
        "people_affected": int(get_field(
            record, ["people_affected", "affected"], 0
        )),
        "severity": int(get_field(
            record, ["severity"], 1
        )),
        "waiting_time_minutes": int(get_field(
            record, ["waiting_time_minutes", "waiting_time"], 0
        )),
        "road_condition": str(get_field(
            record, ["road_condition"], "safe"
        )),
    }

    result["grid_row"] = max(0, min(GRID_SIZE - 1, result["grid_row"]))
    result["grid_col"] = max(0, min(GRID_SIZE - 1, result["grid_col"]))
    result["severity"] = max(1, min(10, result["severity"]))
    return result


def log_event(message):
    st.session_state.event_log.insert(
        0, f"{pd.Timestamp.now().strftime('%H:%M:%S')} — {message}"
    )
    st.session_state.event_log = st.session_state.event_log[:50]


# -------------------- LOAD DATA ----------------------------

def load_data():
    csv_path = Path(__file__).parent / "disaster_dataset.csv"

    if csv_path.exists():
        try:
            data = pd.read_csv(csv_path)
            return [
                normalize_record(x)
                for x in data.to_dict("records")
            ]
        except Exception as error:
            st.error(f"Dataset loading error: {error}")

    if emergency_module is not None:
        source = getattr(emergency_module, "emergencies", [])
        try:
            return [normalize_record(x) for x in source]
        except Exception:
            pass

    return []


if not st.session_state.emergency_data:
    st.session_state.emergency_data = load_data()

# -------------------- FUZZY PRIORITY ENGINE ----------------

def fallback_priority(record):
    severity = record["severity"]
    people = record["people_affected"]
    waiting = record["waiting_time_minutes"]

    score = (
        severity * 7
        + min(people, 1000) / 20
        + min(waiting, 300) / 15
    )
    return min(100, round(score, 2))


def calculate_priority_score(record):
    function = (
        getattr(fuzzy_logic, "calculate_priority", None)
        if fuzzy_logic else None
    )

    if function:
        attempts = [
            lambda: function(record),
            lambda: function(
                record["severity"],
                record["people_affected"],
                record["waiting_time_minutes"]
            ),
            lambda: function(
                severity=record["severity"],
                people_affected=record["people_affected"],
                waiting_time=record["waiting_time_minutes"]
            )
        ]

        for attempt in attempts:
            try:
                value = attempt()

                if isinstance(value, dict):
                    for key in [
                        "priority", "score",
                        "priority_score", "result"
                    ]:
                        if key in value:
                            return float(value[key]), "Project Fuzzy Logic"

                if isinstance(value, (int, float, np.number)):
                    return float(value), "Project Fuzzy Logic"

            except Exception:
                continue

    return fallback_priority(record), "Fallback estimate"


def priority_label(score):
    if score >= 70:
        return "CRITICAL"
    if score >= 45:
        return "HIGH"
    if score >= 20:
        return "MEDIUM"
    return "LOW"


def refresh_priorities():
    for item in st.session_state.emergency_data:
        score, method = calculate_priority_score(item)
        item["priority_score"] = round(score, 2)
        item["priority_level"] = priority_label(score)
        item["priority_method"] = method


refresh_priorities()


# -------------------- GRAPH ENGINE -------------------------

def neighbours(node, blocked):
    r, c = node
    candidates = [
        (r - 1, c), (r + 1, c),
        (r, c - 1), (r, c + 1)
    ]

    return [
        p for p in candidates
        if 0 <= p[0] < GRID_SIZE
        and 0 <= p[1] < GRID_SIZE
        and p not in blocked
    ]


def reconstruct_path(parent, start, goal):
    if goal != start and goal not in parent:
        return []

    path = [goal]
    while path[-1] != start:
        path.append(parent[path[-1]])

    return path[::-1]


def internal_bfs(start, goal, blocked):
    queue = deque([start])
    parent = {}
    visited = {start}

    while queue:
        current = queue.popleft()

        if current == goal:
            return reconstruct_path(parent, start, goal), visited

        for nxt in neighbours(current, blocked):
            if nxt not in visited:
                visited.add(nxt)
                parent[nxt] = current
                queue.append(nxt)

    return [], visited


def internal_dfs(start, goal, blocked):
    stack = [start]
    parent = {}
    visited = {start}

    while stack:
        current = stack.pop()

        if current == goal:
            return reconstruct_path(parent, start, goal), visited

        for nxt in neighbours(current, blocked):
            if nxt not in visited:
                visited.add(nxt)
                parent[nxt] = current
                stack.append(nxt)

    return [], visited


def internal_astar(start, goal, blocked):
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    queue = [(heuristic(start, goal), 0, start)]
    parent = {}
    cost = {start: 0}
    visited = set()

    while queue:
        _, current_cost, current = heapq.heappop(queue)

        if current in visited:
            continue

        visited.add(current)

        if current == goal:
            return reconstruct_path(parent, start, goal), visited

        for nxt in neighbours(current, blocked):
            new_cost = current_cost + 1

            if new_cost < cost.get(nxt, float("inf")):
                cost[nxt] = new_cost
                parent[nxt] = current
                heapq.heappush(
                    queue,
                    (new_cost + heuristic(nxt, goal), new_cost, nxt)
                )

    return [], visited


def calculate_route(name, start, goal, blocked):
    start = clamp_position(start)
    goal = clamp_position(goal)

    external_name = {
        "BFS": "bfs",
        "DFS": "dfs",
        "A*": "astar"
    }[name]

    external = (
        getattr(pathfinding, external_name, None)
        if pathfinding else None
    )

    if external and not blocked:
        try:
            result = external(start, goal)
            if isinstance(result, dict):
                result = result.get("path", result.get("route", []))
            if result:
                return list(result), set(result), "Project module"
        except Exception:
            pass

    if name == "BFS":
        route, visited = internal_bfs(start, goal, blocked)
    elif name == "DFS":
        route, visited = internal_dfs(start, goal, blocked)
    else:
        route, visited = internal_astar(start, goal, blocked)

    return route, visited, "Grid engine"


# -------------------- TEAM ASSIGNMENT ----------------------

def team_locations():
    teams = []

    if isinstance(RESCUE_TEAMS, dict):
        source = RESCUE_TEAMS.items()
    else:
        source = enumerate(RESCUE_TEAMS or [])

    for key, value in source:
        if isinstance(value, dict):
            name = value.get("name", value.get("team_name", str(key)))
            position = coord(value)
            available = value.get("available", True)
        else:
            name = str(key) if isinstance(RESCUE_TEAMS, dict) else f"Team {key + 1}"
            position = coord(value)
            available = True

        if position:
            teams.append({
                "name": name,
                "position": clamp_position(position),
                "available": available
            })

    if not teams:
        teams = [
            {"name": "Alpha Team", "position": (0, 1), "available": True},
            {"name": "Bravo Team", "position": (1, 7), "available": True},
            {"name": "Charlie Team", "position": (7, 1), "available": True},
            {"name": "Delta Team", "position": (6, 6), "available": True}
        ]

    return teams


def assign_rescue_team(record):
    function = (
        getattr(team_assignment, "assign_team", None)
        if team_assignment else None
    )

    if function:
        try:
            result = function(record)
            if isinstance(result, dict):
                return str(
                    result.get("team_name")
                    or result.get("team")
                    or result.get("name")
                    or "Assigned team"
                )
            if result is not None:
                return str(result)
        except Exception:
            pass

    teams = team_locations()
    available = [t for t in teams if t["available"]]

    if not available:
        available = teams

    target = (record["grid_row"], record["grid_col"])

    selected = min(
        available,
        key=lambda t: (
            abs(t["position"][0] - target[0])
            + abs(t["position"][1] - target[1])
        )
    )

    return selected["name"]


# -------------------- DATAFRAME ----------------------------

def dataframe():
    return pd.DataFrame(st.session_state.emergency_data)


# ============================================================
# HEADER + SIDEBAR
# ============================================================

st.title("🚨 RescuePath AI")
st.caption("INTELLIGENT DISASTER RESPONSE & EMERGENCY MANAGEMENT SYSTEM")

with st.sidebar:
    st.title("🚨 RescuePath")
    st.caption("AI Emergency Operations")
    st.divider()

    st.markdown("### System Monitor")
    st.success("Simulation engine online")
    st.write(f"Grid: **{GRID_SIZE} × {GRID_SIZE}**")
    st.write(f"Records: **{len(st.session_state.emergency_data)}**")
    st.write(f"Rescue teams: **{len(team_locations())}**")

    st.divider()
    st.markdown("### Quick Actions")

    if st.button("🔄 Refresh priority scores", use_container_width=True):
        refresh_priorities()
        st.rerun()

    if st.button("🧹 Clear event log", use_container_width=True):
        st.session_state.event_log = []
        st.rerun()

    st.divider()
    st.caption("Educational simulation only. Not a real emergency dispatch system.")

df = dataframe()

if not df.empty:
    df["priority_score"] = pd.to_numeric(
        df["priority_score"], errors="coerce"
    ).fillna(0)

    df["people_affected"] = pd.to_numeric(
        df["people_affected"], errors="coerce"
    ).fillna(0)


# ============================================================
# NAVIGATION
# ============================================================

tabs = st.tabs([
    "🏠 Command Center",
    "🗺️ City Map",
    "🧠 Fuzzy Logic",
    "🚑 Team Management",
    "🧭 Route Intelligence",
    "🚧 Live Rerouting",
    "📊 Analytics Studio",
    "➕ Emergency Control",
    "🗄️ Dataset Explorer",
    "🎮 Simulation"
])


# ============================================================
# 1. COMMAND CENTER
# ============================================================

with tabs[0]:
    st.subheader("Command Center")
    st.caption("Operational overview of all simulated emergencies.")

    total = len(df)
    critical = int((df["priority_level"] == "CRITICAL").sum()) if total else 0
    high = int((df["priority_level"] == "HIGH").sum()) if total else 0
    affected = int(df["people_affected"].sum()) if total else 0
    average_severity = round(df["severity"].mean(), 1) if total else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Incidents", total)
    c2.metric("Critical", critical, delta=None)
    c3.metric("High Priority", high)
    c4.metric("People Affected", f"{affected:,}")
    c5.metric("Avg Severity", f"{average_severity}/10")

    st.divider()

    left, right = st.columns([1.4, 1])

    with left:
        st.markdown("### 🚨 Critical Incident Queue")

        if total:
            urgent = df.sort_values(
                "priority_score", ascending=False
            ).head(8)

            for _, item in urgent.iterrows():
                color = (
                    "🔴" if item["priority_level"] == "CRITICAL"
                    else "🟠" if item["priority_level"] == "HIGH"
                    else "🟡" if item["priority_level"] == "MEDIUM"
                    else "🟢"
                )

                with st.container(border=True):
                    x1, x2, x3 = st.columns([3, 1, 1])
                    x1.markdown(
                        f"**{color} {item['emergency_id']} — "
                        f"{item['disaster_type']}**"
                    )
                    x1.caption(item["location_name"])
                    x2.metric("Score", round(item["priority_score"], 1))
                    x3.metric("Severity", f"{item['severity']}/10")
        else:
            st.info("No incidents currently registered.")

    with right:
        st.markdown("### Priority Distribution")

        if total:
            counts = (
                df["priority_level"]
                .value_counts()
                .reindex(["CRITICAL", "HIGH", "MEDIUM", "LOW"], fill_value=0)
                .reset_index()
            )
            counts.columns = ["Priority", "Incidents"]

            fig = px.pie(
                counts,
                names="Priority",
                values="Incidents",
                hole=0.65,
                color="Priority",
                color_discrete_map={
                    "CRITICAL": "#ff5263",
                    "HIGH": "#ff9e43",
                    "MEDIUM": "#f2d15c",
                    "LOW": "#30c995"
                }
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0c2033",
                margin=dict(t=15, b=15, l=5, r=5)
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Latest System Events")

    if st.session_state.event_log:
        for event in st.session_state.event_log[:8]:
            st.write("•", event)
    else:
        st.caption("No new system events.")


# ============================================================
# 2. INTERACTIVE CITY MAP
# ============================================================

with tabs[1]:
    st.subheader("Interactive City Grid")
    st.caption("Emergency locations, rescue facilities, blocked roads and routes.")

    hospital = coord(HOSPITAL, (0, 0))
    shelter = coord(SHELTER, (GRID_SIZE - 1, GRID_SIZE - 1))

    emergency_positions = {
        (x["grid_row"], x["grid_col"])
        for x in st.session_state.emergency_data
    }

    teams = team_locations()
    blocked = set(st.session_state.blocked_cells)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=[c for r in range(GRID_SIZE) for c in range(GRID_SIZE)],
        y=[r for r in range(GRID_SIZE) for c in range(GRID_SIZE)],
        mode="markers",
        marker=dict(
            symbol="square",
            size=34,
            color="#15324b",
            line=dict(color="#31536d", width=1)
        ),
        hoverinfo="skip",
        showlegend=False
    ))

    def add_marker(position, name, color, symbol, size=18):
        fig.add_trace(go.Scatter(
            x=[position[1]],
            y=[position[0]],
            mode="markers+text",
            text=[name],
            textposition="top center",
            marker=dict(
                size=size,
                color=color,
                symbol=symbol,
                line=dict(color="white", width=1)
            ),
            name=name,
            hovertemplate=f"{name}<extra></extra>"
        ))

    add_marker(hospital, "Hospital", "#35c9f0", "square", 20)
    add_marker(shelter, "Shelter", "#31d49a", "diamond", 20)

    for team in teams:
        add_marker(team["position"], team["name"], "#f5c451", "triangle-up", 16)

    if emergency_positions:
        fig.add_trace(go.Scatter(
            x=[p[1] for p in emergency_positions],
            y=[p[0] for p in emergency_positions],
            mode="markers",
            marker=dict(
                size=16,
                color="#ff5263",
                symbol="x",
                line=dict(width=2)
            ),
            name="Emergencies"
        ))

    if blocked:
        fig.add_trace(go.Scatter(
            x=[p[1] for p in blocked],
            y=[p[0] for p in blocked],
            mode="markers",
            marker=dict(size=17, color="#747e8a", symbol="square"),
            name="Blocked Roads"
        ))

    route = st.session_state.active_route
    if route:
        fig.add_trace(go.Scatter(
            x=[p[1] for p in route],
            y=[p[0] for p in route],
            mode="lines+markers",
            line=dict(color="#28d9ed", width=5),
            marker=dict(size=7, color="#ffffff"),
            name="Selected Route"
        ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0c2033",
        plot_bgcolor="#091827",
        height=650,
        xaxis=dict(
            title="Grid Column",
            tickmode="linear",
            dtick=1,
            range=[-0.5, GRID_SIZE - 0.5]
        ),
        yaxis=dict(
            title="Grid Row",
            tickmode="linear",
            dtick=1,
            autorange="reversed",
            range=[GRID_SIZE - 0.5, -0.5],
            scaleanchor="x"
        ),
        legend=dict(orientation="h", y=-0.12),
        margin=dict(l=20, r=20, t=25, b=60)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        "**Legend:** 🔵 Hospital · 🟢 Shelter · 🟡 Rescue teams · "
        "🔴 Emergencies · ⬛ Blocked roads · Cyan line = route"
    )

    if route:
        st.success(f"Active route contains {len(route)} grid positions.")


# ============================================================
# 3. FUZZY LOGIC ENGINE
# ============================================================

with tabs[2]:
    st.subheader("Fuzzy Logic Priority Engine")
    st.caption("Explore how severity, affected population and waiting time influence priority.")

    if df.empty:
        st.info("Register an emergency to explore its priority.")
    else:
        selected_id = st.selectbox(
            "Choose incident",
            df["emergency_id"].astype(str).tolist(),
            key="fuzzy_select"
        )

        record = next(
            x for x in st.session_state.emergency_data
            if str(x["emergency_id"]) == selected_id
        )

        score, method = calculate_priority_score(record)
        level = priority_label(score)

        a, b, c = st.columns(3)
        a.metric("Severity Input", f"{record['severity']}/10")
        b.metric("People Affected", record["people_affected"])
        c.metric("Waiting Time", f"{record['waiting_time_minutes']} min")

        st.divider()

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=min(100, max(0, score)),
            title={"text": "Emergency Priority Score"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#27cbe2"},
                "steps": [
                    {"range": [0, 20], "color": "#1f805e"},
                    {"range": [20, 45], "color": "#a48a34"},
                    {"range": [45, 70], "color": "#b96d35"},
                    {"range": [70, 100], "color": "#a63c50"}
                ]
            }
        ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0c2033",
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"### Priority classification: **{level}**")
        st.write(f"Calculation source: `{method}`")

        breakdown = pd.DataFrame({
            "Input": ["Severity", "People affected", "Waiting time"],
            "Value": [
                record["severity"],
                record["people_affected"],
                record["waiting_time_minutes"]
            ]
        })

        fig = px.bar(
            breakdown,
            x="Input",
            y="Value",
            color="Input",
            text="Value"
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0c2033",
            plot_bgcolor="#0c2033",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        st.info(
            "The displayed fallback score is a demonstration estimate, "
            "not a validated real-world emergency triage score."
        )


# ============================================================
# 4. RESCUE TEAM MANAGEMENT
# ============================================================

with tabs[3]:
    st.subheader("Rescue Team Management")

    teams = team_locations()

    st.markdown("### Team Fleet")

    cols = st.columns(min(4, len(teams)))

    for i, team in enumerate(teams):
        with cols[i % len(cols)]:
            with st.container(border=True):
                st.markdown(f"### 🚑 {team['name']}")
                st.write(f"Position: `{team['position']}`")
                st.success("Available" if team["available"] else "Unavailable")

                workloads = [
                    name for name, assigned in
                    st.session_state.assigned_teams.items()
                    if assigned == team["name"]
                ]
                st.metric("Assigned incidents", len(workloads))

    st.divider()
    st.markdown("### Assign Team to Emergency")

    if not df.empty:
        selected_id = st.selectbox(
            "Select emergency",
            df["emergency_id"].astype(str).tolist(),
            key="team_select"
        )

        selected = next(
            x for x in st.session_state.emergency_data
            if str(x["emergency_id"]) == selected_id
        )

        if st.button("⚡ Assign Nearest Available Team"):
            team_name = assign_rescue_team(selected)
            st.session_state.assigned_teams[selected_id] = team_name
            log_event(f"{team_name} assigned to {selected_id}")
            st.success(f"{team_name} assigned successfully.")

        if selected_id in st.session_state.assigned_teams:
            st.info(
                f"Current assignment: "
                f"{st.session_state.assigned_teams[selected_id]}"
            )

    st.markdown("### Assignment Register")

    if st.session_state.assigned_teams:
        assignment_df = pd.DataFrame([
            {"Emergency ID": key, "Assigned Team": value}
            for key, value in st.session_state.assigned_teams.items()
        ])
        st.dataframe(assignment_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No team assignments yet.")


# ============================================================
# 5. ROUTE INTELLIGENCE
# ============================================================

with tabs[4]:
    st.subheader("Route Intelligence")
    st.caption("Compare BFS, DFS and A* on the same city grid.")

    if not df.empty:
        selected_id = st.selectbox(
            "Destination emergency",
            df["emergency_id"].astype(str).tolist(),
            key="route_select"
        )

        selected = next(
            x for x in st.session_state.emergency_data
            if str(x["emergency_id"]) == selected_id
        )

        start = coord(HOSPITAL, (0, 0))
        goal = (selected["grid_row"], selected["grid_col"])

        st.write(f"**Start:** {start} → **Destination:** {goal}")

        blocked = set(st.session_state.blocked_cells)

        results = {}

        for algorithm in ["BFS", "DFS", "A*"]:
            route, visited, engine = calculate_route(
                algorithm, start, goal, blocked
            )
            results[algorithm] = {
                "route": route,
                "visited": visited,
                "engine": engine
            }

        comparison = []

        for algorithm, result in results.items():
            comparison.append({
                "Algorithm": algorithm,
                "Path length": len(result["route"]),
                "Nodes explored": len(result["visited"]),
                "Status": "Found" if result["route"] else "No path"
            })

        comparison_df = pd.DataFrame(comparison)
        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True
        )

        fig = px.bar(
            comparison_df,
            x="Algorithm",
            y=["Path length", "Nodes explored"],
            barmode="group",
            title="Algorithm Performance Comparison"
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0c2033",
            plot_bgcolor="#0c2033"
        )
        st.plotly_chart(fig, use_container_width=True)

        algorithm = st.radio(
            "Visualize route",
            ["BFS", "DFS", "A*"],
            horizontal=True
        )

        selected_result = results[algorithm]

        if selected_result["route"]:
            st.success(
                f"{algorithm} route found with "
                f"{len(selected_result['route'])} positions."
            )

            if st.button("Show this route on City Map"):
                st.session_state.active_route = selected_result["route"]
                st.session_state.route_algorithm = algorithm
                st.success("Route selected. Open the City Map tab.")
        else:
            st.error("No route found with the current blocked roads.")

        st.caption(
            "The internal grid engine is used when the project's pathfinding "
            "function cannot be called with the expected interface."
        )
    else:
        st.info("No emergency destinations available.")


# ============================================================
# 6. LIVE REROUTING
# ============================================================

with tabs[5]:
    st.subheader("Live Road Blockage & Rerouting")
    st.caption("Block a grid cell and calculate an alternative route.")

    left, right = st.columns(2)

    with left:
        block_row = st.number_input(
            "Blocked road row",
            0, GRID_SIZE - 1, 3,
            key="block_row"
        )

    with right:
        block_col = st.number_input(
            "Blocked road column",
            0, GRID_SIZE - 1, 3,
            key="block_col"
        )

    blocked_position = (int(block_row), int(block_col))

    if st.button("🚧 Block Selected Road"):
        if blocked_position not in st.session_state.blocked_cells:
            st.session_state.blocked_cells.append(blocked_position)
            log_event(f"Road blocked at {blocked_position}")
            st.success(f"Road blocked at {blocked_position}")
        else:
            st.warning("That road is already blocked.")

    if st.button("🟢 Reopen Selected Road"):
        if blocked_position in st.session_state.blocked_cells:
            st.session_state.blocked_cells.remove(blocked_position)
            log_event(f"Road reopened at {blocked_position}")
            st.success("Road reopened.")
        else:
            st.info("This road is not blocked.")

    if st.button("Reset All Blocked Roads"):
        st.session_state.blocked_cells = []
        st.session_state.alternative_route = []
        log_event("All manually blocked roads cleared")
        st.success("Blocked roads cleared.")

    st.write("**Currently blocked cells:**")
    st.write(st.session_state.blocked_cells or "None")

    st.divider()

    if not df.empty:
        selected_id = st.selectbox(
            "Emergency destination",
            df["emergency_id"].astype(str).tolist(),
            key="reroute_select"
        )

        selected = next(
            x for x in st.session_state.emergency_data
            if str(x["emergency_id"]) == selected_id
        )

        start = coord(HOSPITAL, (0, 0))
        goal = (selected["grid_row"], selected["grid_col"])

        if st.button("🔁 Calculate Alternative Route"):
            route, visited = internal_astar(
                start, goal, set(st.session_state.blocked_cells)
            )

            external = (
                getattr(rerouting, "find_alternative_route", None)
                if rerouting else None
            )

            if external:
                try:
                    candidate = external(
                        start, goal, blocked_position
                    )
                    if isinstance(candidate, dict):
                        candidate = candidate.get(
                            "path", candidate.get("route", [])
                        )
                    if candidate:
                        route = list(candidate)
                except Exception:
                    pass

            st.session_state.alternative_route = route
            st.session_state.active_route = route

            if route:
                log_event(f"Alternative route calculated for {selected_id}")
                st.success(f"Alternative route found: {len(route)} positions.")
            else:
                st.error("No alternative route is available.")

        if st.session_state.alternative_route:
            st.markdown("### Alternative Route")
            st.code(
                " → ".join(
                    str(x) for x in st.session_state.alternative_route
                )
            )


# ============================================================
# 7. ANALYTICS STUDIO
# ============================================================

with tabs[6]:
    st.subheader("Analytics Studio")

    if df.empty:
        st.info("No records available for analytics.")
    else:
        all_types = sorted(df["disaster_type"].dropna().unique().tolist())

        selected_types = st.multiselect(
            "Filter disaster types",
            all_types,
            default=all_types
        )

        filtered = df[
            df["disaster_type"].isin(selected_types)
        ].copy()

        st.write(f"Showing {len(filtered)} of {len(df)} incidents.")

        a, b = st.columns(2)

        with a:
            st.markdown("### Incidents by Disaster Type")
            type_counts = (
                filtered["disaster_type"]
                .value_counts()
                .reset_index()
            )
            type_counts.columns = ["Disaster", "Count"]

            fig = px.bar(
                type_counts,
                x="Disaster",
                y="Count",
                color="Disaster",
                text="Count"
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0c2033",
                plot_bgcolor="#0c2033",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        with b:
            st.markdown("### People Affected")
            affected = (
                filtered.groupby("disaster_type")["people_affected"]
                .sum()
                .reset_index()
            )

            fig = px.pie(
                affected,
                names="disaster_type",
                values="people_affected",
                hole=0.5
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0c2033"
            )
            st.plotly_chart(fig, use_container_width=True)

        a, b = st.columns(2)

        with a:
            st.markdown("### Severity Distribution")
            fig = px.histogram(
                filtered,
                x="severity",
                color="disaster_type",
                nbins=10
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0c2033",
                plot_bgcolor="#0c2033"
            )
            st.plotly_chart(fig, use_container_width=True)

        with b:
            st.markdown("### Waiting Time vs Priority")
            fig = px.scatter(
                filtered,
                x="waiting_time_minutes",
                y="priority_score",
                color="priority_level",
                size="people_affected",
                hover_name="location_name"
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0c2033",
                plot_bgcolor="#0c2033"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Severity and Priority Relationship")

        # FIX: Removed trendline="ols" because it requires statsmodels.
        fig = px.scatter(
            filtered,
            x="severity",
            y="priority_score",
            color="disaster_type",
            size="people_affected",
            hover_name="location_name"
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0c2033",
            plot_bgcolor="#0c2033"
        )
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# 8. EMERGENCY CONTROL PANEL
# ============================================================

with tabs[7]:
    st.subheader("Emergency Control Panel")
    st.caption("Register and manage simulated emergency incidents.")

    with st.form("register_emergency", clear_on_submit=True):
        c1, c2 = st.columns(2)

        with c1:
            disaster_type = st.selectbox(
                "Disaster Type",
                ["Flood", "Earthquake", "Accident", "Fire",
                 "Landslide", "Storm", "Other"]
            )

            location_name = st.text_input("Location Name")

            severity = st.slider("Severity", 1, 10, 5)

            people = st.number_input(
                "People Affected", 1, 100000, 10
            )

        with c2:
            row = st.number_input(
                "Grid Row", 0, GRID_SIZE - 1, 2
            )
            col = st.number_input(
                "Grid Column", 0, GRID_SIZE - 1, 2
            )
            waiting = st.number_input(
                "Waiting Time (minutes)", 0, 10000, 10
            )
            road = st.selectbox(
                "Road Condition", ["safe", "risky", "blocked"]
            )

        submitted = st.form_submit_button(
            "➕ Register Emergency",
            use_container_width=True
        )

    if submitted:
        if not location_name.strip():
            st.error("Please enter a location name.")
        else:
            st.session_state.manual_emergency_counter += 1

            new_record = normalize_record({
                "emergency_id": (
                    f"MAN-{st.session_state.manual_emergency_counter:03d}"
                ),
                "disaster_type": disaster_type,
                "location_name": location_name.strip(),
                "grid_row": int(row),
                "grid_col": int(col),
                "people_affected": int(people),
                "severity": int(severity),
                "waiting_time_minutes": int(waiting),
                "road_condition": road,
                "record_origin": "Manual Entry"
            })

            st.session_state.emergency_data.append(new_record)
            refresh_priorities()
            log_event(f"New emergency registered: {new_record['emergency_id']}")
            st.success(
                f"Emergency {new_record['emergency_id']} registered."
            )
            st.rerun()

    st.divider()
    st.markdown("### Manage Existing Incidents")

    if not df.empty:
        selected_id = st.selectbox(
            "Select record to manage",
            df["emergency_id"].astype(str).tolist(),
            key="manage_select"
        )

        selected_index = next(
            i for i, x in enumerate(st.session_state.emergency_data)
            if str(x["emergency_id"]) == selected_id
        )

        selected = st.session_state.emergency_data[selected_index]

        with st.container(border=True):
            st.write(f"**{selected['emergency_id']}**")
            st.write(
                f"{selected['disaster_type']} — "
                f"{selected['location_name']}"
            )
            st.write(
                f"Priority: {selected.get('priority_level', 'Unknown')}"
            )

            if st.button("Delete Selected Incident"):
                removed = st.session_state.emergency_data.pop(selected_index)
                st.session_state.assigned_teams.pop(selected_id, None)
                log_event(f"Incident deleted: {selected_id}")
                st.success(f"{removed['emergency_id']} deleted.")
                st.rerun()


# ============================================================
# 9. DATASET EXPLORER
# ============================================================

with tabs[8]:
    st.subheader("Dataset Explorer")
    st.caption("Search, filter, inspect and export emergency records.")

    current_df = dataframe()

    if current_df.empty:
        st.info("No records found.")
    else:
        search = st.text_input(
            "Search dataset",
            placeholder="Search ID, location or disaster type..."
        )

        filtered = current_df.copy()

        if search.strip():
            mask = filtered.astype(str).apply(
                lambda col: col.str.contains(
                    search, case=False, na=False
                )
            ).any(axis=1)
            filtered = filtered[mask]

        types = sorted(filtered["disaster_type"].dropna().unique().tolist())

        selected_types = st.multiselect(
            "Disaster type filter",
            types,
            default=types,
            key="dataset_types"
        )

        filtered = filtered[
            filtered["disaster_type"].isin(selected_types)
        ]

        severity_range = st.slider(
            "Severity range",
            1, 10, (1, 10),
            key="dataset_severity"
        )

        filtered = filtered[
            (filtered["severity"] >= severity_range[0])
            & (filtered["severity"] <= severity_range[1])
        ]

        st.metric("Matching Records", len(filtered))

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )

        csv = filtered.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Download Filtered CSV",
            data=csv,
            file_name="rescuepath_filtered_dataset.csv",
            mime="text/csv"
        )


# ============================================================
# 10. SIMULATION CONTROL
# ============================================================

with tabs[9]:
    st.subheader("Disaster Simulation Lab")
    st.caption("Run a controlled demonstration of emergency response operations.")

    st.markdown("### Simulation Controls")

    c1, c2, c3 = st.columns(3)

    with c1:
        simulation_speed = st.select_slider(
            "Simulation speed",
            options=["Slow", "Normal", "Fast"],
            value="Normal"
        )

    with c2:
        scenario = st.selectbox(
            "Scenario",
            ["Flood Response", "Earthquake Response",
             "Fire Response", "Multi-Incident Response"]
        )

    with c3:
        simulation_steps = st.number_input(
            "Simulation steps",
            1, 20, 5
        )

    if st.button("▶ Run Simulation"):
        st.session_state.simulation_running = True
        st.session_state.simulation_tick += 1

        log_event(
            f"Simulation started: {scenario}, "
            f"{simulation_steps} steps, {simulation_speed} speed"
        )

        module_function = None

        if simulation is not None:
            for function_name in [
                "run_simulation", "simulate", "start_simulation"
            ]:
                candidate = getattr(simulation, function_name, None)
                if callable(candidate):
                    module_function = candidate
                    break

        if module_function:
            try:
                signature = inspect.signature(module_function)
                kwargs = {}

                for name in signature.parameters:
                    if name in ["steps", "num_steps"]:
                        kwargs[name] = int(simulation_steps)
                    elif name in ["scenario", "disaster_type"]:
                        kwargs[name] = scenario

                result = module_function(**kwargs)
                st.session_state["simulation_result"] = str(result)
            except Exception as error:
                st.session_state["simulation_result"] = (
                    f"Module simulation could not run: {error}"
                )
        else:
            st.session_state["simulation_result"] = (
                "Dashboard demonstration simulation completed. "
                "No compatible simulation function was found in simulation.py."
            )

        st.session_state.simulation_running = False

    if "simulation_result" in st.session_state:
        st.success("Simulation process finished.")
        st.write(st.session_state.simulation_result)

    st.divider()
    st.markdown("### Simulation Summary")

    s1, s2, s3 = st.columns(3)
    s1.metric("Simulation Runs", st.session_state.simulation_tick)
    s2.metric("Current Incidents", len(st.session_state.emergency_data))
    s3.metric("Blocked Roads", len(st.session_state.blocked_cells))

    st.markdown("### Event Timeline")

    if st.session_state.event_log:
        for event in st.session_state.event_log[:15]:
            st.write("•", event)
    else:
        st.caption("No simulation events yet.")


# ============================================================
# FOOTER
# ============================================================

st.divider()

left, right = st.columns(2)

with left:
    st.caption("RESCUEPATH AI · DISASTER RESPONSE SIMULATION")

with right:
    st.caption("Fuzzy Logic · BFS · DFS · A* · Team Assignment · Rerouting")
