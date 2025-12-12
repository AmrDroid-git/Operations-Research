from typing import Tuple
from itertools import combinations
from gurobipy import Model, GRB, quicksum

# ------------------------------------------------------------------
# INPUT DATA
events = [
    {"event": "math",    "duration": "09:00 -> 10:00"},
    {"event": "physics", "duration": "09:30 -> 11:00"},
    {"event": "chem",    "duration": "10:00 -> 11:00"},
    {"event": "bio",     "duration": "11:30 -> 12:30"},
]
# ------------------------------------------------------------------


# -------------------- 1. Time Parsing --------------------
def to_hours(t: str) -> float:
    h, m = map(int, t.split(":"))
    return h + m / 60


def overlap(i1: Tuple[float, float], i2: Tuple[float, float]) -> bool:
    s1, e1 = i1
    s2, e2 = i2
    return s1 < e2 and s2 < e1


# -------------------- 2. Convert durations to numeric --------------------
event_times = {}
for e in events:
    start_str, end_str = e["duration"].split(" -> ")
    event_times[e["event"]] = (to_hours(start_str), to_hours(end_str))

V = list(event_times.keys())

print("V= ",V)

# -------------------- 3. Build conflict graph --------------------
E = []
for u, v in combinations(V, 2):
    if overlap(event_times[u], event_times[v]):
        E.append((u, v))

print("E= ",E)

# -------------------- 4. Optimal Coloring with Gurobi --------------------
K = len(V)   # max possible colors
m = Model("coloring")
m.Params.OutputFlag = 0 #bech ma nchoufech leklem el fere8 mta3 el progress

# x[v,k] = 1 if event v gets color k
x = m.addVars(V, range(K), vtype=GRB.BINARY, name="x")

# y[k] = 1 if color k is used
y = m.addVars(range(K), vtype=GRB.BINARY, name="y")

# each vertex has exactly one color
m.addConstrs((quicksum(x[v, k] for k in range(K)) == 1 for v in V))

# link: cannot use color unless activated
m.addConstrs((x[v, k] <= y[k] for v in V for k in range(K)))

# adjacent conflicts
for u, v in E:
    for k in range(K):
        m.addConstr(x[u, k] + x[v, k] <= y[k])

m.setObjective(quicksum(y[k] for k in range(K)), GRB.MINIMIZE)
m.optimize()


# -------------------- 5. Extract optimal colors --------------------
colours = {}
for v in V:
    for k in range(K):
        if x[v, k].X > 0.5:
            colours[v] = k
            break

used = sorted(k for k in range(K) if y[k].X > 0.5)
color_map = {used[i]: f"A{i+1}" for i in range(len(used))}


# -------------------- 6. Assign class to each event --------------------
for e in events:
    e["class"] = color_map[colours[e["event"]]]

# -------------------- 7. Print result --------------------
for e in events:
    print(f"{e['event']:10s}  {e['duration']:17s}  ->  {e['class']}")
