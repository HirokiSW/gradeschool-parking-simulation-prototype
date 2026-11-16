import os
import random
import sumolib
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NET = os.path.join(BASE, "network", "gradeschoolarea.net.xml")
ADD_FILE = os.path.join(BASE, "additional", "gradeschoolarea.add.xml")
OUT_DIR = os.path.join(BASE, "routes")
OUT_FILE = os.path.join(OUT_DIR, "routes_1_school_bus.rou.xml")

random.seed(1)
N_BUSES = 95
BUS_AREAS = ["pa_2", "pa_3"]
ENTRY = "1237202658"                       # gate 2
EXITS = ["205611785", "313786478#1"]       # gate 2.5, outside campus
EXIT_WEIGHTS = [0.5, 0.5]
LAST_DEPART = 2400                         # seconds, buses arrive in the first 40 min
STAY_MIN, STAY_MAX = 300, 900              # 5 to 15 minutes
BUS_LENGTH = 5.0                           # raise to about 9 for bus-sized vehicles

net = sumolib.net.readNet(NET)

for e in [ENTRY] + EXITS:
    if not net.hasEdge(e):
        raise SystemExit("Edge not in network: " + e)

areas = {}
for pa in ET.parse(ADD_FILE).getroot().iter("parkingArea"):
    if pa.get("id") in BUS_AREAS:
        cap = int(pa.get("roadsideCapacity", 0)) or len(list(pa.iter("space"))) or 1
        edge = pa.get("lane").rsplit("_", 1)[0]
        areas[pa.get("id")] = (edge, cap)

print("Bus areas found:", areas, "total spots:", sum(c for _, c in areas.values()))
if not areas:
    raise SystemExit("No bus areas found. Check BUS_AREAS and ADD_FILE.")

def reachable(a, b):
    path, _ = net.getShortestPath(net.getEdge(a), net.getEdge(b), vClass="bus")
    return path is not None

ok_areas = [(pid, e, c) for pid, (e, c) in areas.items()
            if reachable(ENTRY, e) and any(reachable(e, x) for x in EXITS)]
print("Reachable bus areas:", [a[0] for a in ok_areas])
if not ok_areas:
    raise SystemExit("No bus area is reachable from the entry. Check connections.")

departs = sorted(random.uniform(0, LAST_DEPART) for _ in range(N_BUSES))

root = ET.Element("routes")
ET.SubElement(root, "vType", id="school_bus", vClass="bus",
              color="1,1,0", length=str(BUS_LENGTH), guiShape="bus")

skipped = 0
count = 0
for t in departs:
    pid, edge, cap = random.choices(ok_areas, [a[2] for a in ok_areas])[0]
    exits = [(x, w) for x, w in zip(EXITS, EXIT_WEIGHTS) if reachable(edge, x)]
    if not exits:
        skipped += 1
        continue
    dst = random.choices([x for x, _ in exits], [w for _, w in exits])[0]
    trip = ET.SubElement(root, "trip", id=f"bus_{count}", type="school_bus",
                         depart=f"{t:.1f}", attrib={"from": ENTRY, "to": dst})
    stop = ET.SubElement(trip, "stop")
    stop.set("parkingArea", pid)
    stop.set("duration", str(random.randint(STAY_MIN, STAY_MAX)))
    count += 1

os.makedirs(OUT_DIR, exist_ok=True)
ET.indent(root)
ET.ElementTree(root).write(OUT_FILE)
print(count, "buses written,", skipped, "skipped. File:", OUT_FILE)