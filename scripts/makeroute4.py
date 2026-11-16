import os
import random
from functools import lru_cache
import sumolib
import xml.etree.ElementTree as ET

SURGE_START = 1800      # seconds, the last 30 minutes
SURGE_SHARE = 0.7       # 70% depart after SURGE_START, use 0.67 to 0.75

def make_departs(n, first, last):
    out = []
    for _ in range(n):
        if first >= SURGE_START or last <= SURGE_START:
            out.append(random.uniform(first, last))
        elif random.random() < SURGE_SHARE:
            out.append(random.uniform(SURGE_START, last))
        else:
            out.append(random.uniform(first, SURGE_START))
    return sorted(out)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NET = os.path.join(BASE, "network", "gradeschoolarea.net.xml")
ADD_FILE = os.path.join(BASE, "additional", "gradeschoolarea.add.xml")
OUT_DIR = os.path.join(BASE, "routes")
OUT_FILE = os.path.join(OUT_DIR, "routes_4_parked_dropoffs.rou.xml")

random.seed(4)
N_VEHICLES = 200                     
LAST_DEPART = 3000                   # seconds
STAY_MIN, STAY_MAX = 300, 900        # 5 to 15 minutes

ENTRIES = ["1237202658", "360817894#1.24", "583962451#0.114"]
ENTRY_WEIGHTS = [0.7, 0.15, 0.15]
EXITS = ["205611785", "313786478#1"]
EXIT_WEIGHTS = [0.5, 0.5]

GROUPS = {
    "p1": ["pa_0", "pa_1"],
    "gym": ["pa_34", "pa_35"],
    "p2p3": ["pa_15", "pa_18", "pa_19", "pa_20", "pa_21"],
    "p4p5": ["pa_9", "pa_11"],
    "p6": ["pa_13", "pa_36", "pa_12", "pa_38", "pa_14", "pa_16", "pa_33"],
    "p7": ["pa_4", "pa_5", "pa_6", "pa_37"],
    "central": ["pa_39", "pa_22", "pa_23", "pa_17", "pa_24", "pa_25", "pa_26",
                "pa_27", "pa_28", "pa_29", "pa_30", "pa_31", "pa_32"],
}
PREFERRED = {
    "1237202658": ["p1", "p2p3", "p7"],
    "360817894#1.24": ["beg", "p4p5", "p6", "p7"],
    "583962451#0.114": ["central", "p6"],
}
PREFERRED_SHARE = 0.75    # share that go to a preferred group
GYM_WEIGHT = 0.05         # gym is rarely the first pick

net = sumolib.net.readNet(NET)
for e in ENTRIES + EXITS:
    if not net.hasEdge(e):
        raise SystemExit("Edge not in network: " + e)

areas = {}
for pa in ET.parse(ADD_FILE).getroot().iter("parkingArea"):
    cap = int(pa.get("roadsideCapacity", 0)) or len(list(pa.iter("space"))) or 1
    areas[pa.get("id")] = (pa.get("lane").rsplit("_", 1)[0], cap)

for g, ids in GROUPS.items():
    for pid in ids:
        if pid not in areas:
            raise SystemExit("Parking area not found: " + pid)
    print(g, "spots:", sum(areas[p][1] for p in ids))

@lru_cache(maxsize=None)
def reachable(a, b):
    path, _ = net.getShortestPath(net.getEdge(a), net.getEdge(b), vClass="passenger")
    return path is not None

def usable(entry, pid):
    edge = areas[pid][0]
    return reachable(entry, edge) and any(reachable(edge, x) for x in EXITS)

def pick_area(entry):
    ok = {g: [p for p in ids if usable(entry, p)] for g, ids in GROUPS.items()}
    ok = {g: ids for g, ids in ok.items() if ids}
    if not ok:
        return None
    pref = [g for g in PREFERRED[entry] if g in ok]
    if pref and random.random() < PREFERRED_SHARE:
        group = random.choice(pref)
    else:
        names = list(ok)
        weights = [GYM_WEIGHT if g == "gym" else 1 for g in names]
        group = random.choices(names, weights)[0]
    ids = ok[group]
    return random.choices(ids, [areas[p][1] for p in ids])[0]
    
departs = make_departs(N_VEHICLES, 0, LAST_DEPART)

root = ET.Element("routes")
ET.SubElement(root, "vType", id="parked_dropoff", vClass="passenger", color="1,0.55,0")

count = skipped = 0
for t in departs:
    entry = random.choices(ENTRIES, ENTRY_WEIGHTS)[0]
    pid = pick_area(entry)
    if pid is None:
        skipped += 1
        continue
    edge = areas[pid][0]
    exits = [(x, w) for x, w in zip(EXITS, EXIT_WEIGHTS) if reachable(edge, x)]
    dst = random.choices([x for x, _ in exits], [w for _, w in exits])[0]
    trip = ET.SubElement(root, "trip", id=f"pdrop_{count}", type="parked_dropoff",
                         depart=f"{t:.1f}", attrib={"from": entry, "to": dst})
    stop = ET.SubElement(trip, "stop")
    stop.set("parkingArea", pid)
    stop.set("duration", str(random.randint(STAY_MIN, STAY_MAX)))
    count += 1

os.makedirs(OUT_DIR, exist_ok=True)
ET.indent(root)
ET.ElementTree(root).write(OUT_FILE)
print(count, "parked dropoffs written,", skipped, "skipped. File:", OUT_FILE)