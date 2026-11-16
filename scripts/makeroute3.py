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
OUT_FILE = os.path.join(OUT_DIR, "routes_3_dropoffs.rou.xml")

random.seed(3)
N_VEHICLES = 800
LAST_DEPART = 3300
STOP_MIN, STOP_MAX = 60, 90
NEAR_SHARE = 0.9

DROP_AREAS = ["pa_40", "pa_41", "pa_42", "pa_44", "pa_45"]
REDIRECT = {"pa_40": "pa_41"}
ENTRIES = ["1237202658", "360817894#1.24", "583962451#0.114"]
ENTRY_WEIGHTS = [0.7, 0.15, 0.15]
EXITS = ["205611785", "313786478#1"]
EXIT_WEIGHTS = [0.5, 0.5]

GATE2_LANES = ["1312076548#0_0", "1312076548#1_0", "30970361#1_0", "E0_0"]
NEAR_LANES = {
    "1237202658": GATE2_LANES,
    "360817894#1.24": ["46522214#1_1"],
    "583962451#0.114": ["207134388_0"],
}

net = sumolib.net.readNet(NET)
for e in ENTRIES + EXITS:
    if not net.hasEdge(e):
        raise SystemExit("Edge not in network: " + e)

areas = {}
for pa in ET.parse(ADD_FILE).getroot().iter("parkingArea"):
    if pa.get("id") in DROP_AREAS:
        cap = int(pa.get("roadsideCapacity", 0)) or len(list(pa.iter("space"))) or 1
        lane = pa.get("lane")
        areas[pa.get("id")] = (lane, lane.rsplit("_", 1)[0], cap)

for pid in DROP_AREAS:
    if pid not in areas:
        raise SystemExit("Parking area not found: " + pid)
    print(pid, "lane", areas[pid][0], "capacity", areas[pid][2])
print("Total drop-off capacity:", sum(a[2] for a in areas.values()))

@lru_cache(maxsize=None)
def reachable(a, b):
    path, _ = net.getShortestPath(net.getEdge(a), net.getEdge(b), vClass="passenger")
    return path is not None

def usable(entry, pid):
    edge = areas[pid][1]
    return reachable(entry, edge) and any(reachable(edge, x) for x in EXITS)

usable_areas = {en: [p for p in DROP_AREAS if usable(en, p)] for en in ENTRIES}
near_areas = {en: [p for p in usable_areas[en] if areas[p][0] in NEAR_LANES[en]]
              for en in ENTRIES}
for en in ENTRIES:
    print("Entry", en, "near:", near_areas[en], "usable:", usable_areas[en])

departs = make_departs(N_VEHICLES, 0, LAST_DEPART)

root = ET.Element("routes")
ET.SubElement(root, "vType", id="dropoff", vClass="passenger", color="0,0.8,0.2")

count = skipped = 0
for t in departs:
    entry = random.choices(ENTRIES, ENTRY_WEIGHTS)[0]
    pool = near_areas[entry] if near_areas[entry] and random.random() < NEAR_SHARE \
        else usable_areas[entry]
    if not pool:
        skipped += 1
        continue
    pid = random.choices(pool, [areas[p][2] for p in pool])[0]
    pid = REDIRECT.get(pid, pid)
    if not usable(entry, pid):
        skipped += 1
        continue
    edge = areas[pid][1]
    exits = [(x, w) for x, w in zip(EXITS, EXIT_WEIGHTS) if reachable(edge, x)]
    dst = random.choices([x for x, _ in exits], [w for _, w in exits])[0]
    trip = ET.SubElement(root, "trip", id=f"drop_{count}", type="dropoff",
                         depart=f"{t:.1f}", attrib={"from": entry, "to": dst})
    stop = ET.SubElement(trip, "stop")
    stop.set("parkingArea", pid)
    stop.set("duration", str(random.randint(STOP_MIN, STOP_MAX)))
    count += 1

os.makedirs(OUT_DIR, exist_ok=True)
ET.indent(root)
ET.ElementTree(root).write(OUT_FILE)
print(count, "dropoffs written,", skipped, "skipped. File:", OUT_FILE)