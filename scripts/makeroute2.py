import os
import random
import sumolib
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NET = os.path.join(BASE, "network", "gradeschoolarea.net.xml")
ADD_FILE = os.path.join(BASE, "additional", "gradeschoolarea.add.xml")
OUT_DIR = os.path.join(BASE, "routes")
OUT_FILE = os.path.join(OUT_DIR, "routes_2_faculty.rou.xml")
RR_FILE = os.path.join(BASE, "additional", "rerouter_faculty.add.xml")

random.seed(2)
N_FACULTY = 50
FAC_AREAS = ["pa_7", "pa_8", "pa_10"]
GENERAL = ["pa_0", "pa_1", "pa_34", "pa_35", "pa_15", "pa_18", "pa_19", "pa_20",
           "pa_21", "pa_9", "pa_11", "pa_13", "pa_36", "pa_12", "pa_38", "pa_14",
           "pa_16", "pa_33", "pa_4", "pa_5", "pa_6", "pa_37", "pa_39", "pa_22",
           "pa_23", "pa_17", "pa_24", "pa_25", "pa_26", "pa_27", "pa_28", "pa_29",
           "pa_30", "pa_31", "pa_32"]
ENTRIES = ["1237202658", "360817894#1.24", "583962451#0.114"]
ENTRY_WEIGHTS = [0.6, 0.2, 0.2]
EXITS = ["205611785", "313786478#1", "-935386041#0"]   # never reached, cars park for good
LAST_DEPART = 1800
STAY = 100000
K = 5
WRITE_REROUTER = True

net = sumolib.net.readNet(NET)
for e in ENTRIES + EXITS:
    if not net.hasEdge(e):
        raise SystemExit("Edge not in network: " + e)

areas = {}
for pa in ET.parse(ADD_FILE).getroot().iter("parkingArea"):
    cap = int(pa.get("roadsideCapacity", 0)) or len(list(pa.iter("space"))) or 1
    areas[pa.get("id")] = (pa.get("lane").rsplit("_", 1)[0], cap)

for pid in FAC_AREAS:
    if pid not in areas:
        raise SystemExit("Parking area not found: " + pid)
print("Faculty areas:", {p: areas[p] for p in FAC_AREAS},
      "total spots:", sum(areas[p][1] for p in FAC_AREAS))

def cost(a, b):
    path, c = net.getShortestPath(net.getEdge(a), net.getEdge(b), vClass="passenger")
    return None if path is None else c

targets = []
for pid in FAC_AREAS:
    targets += [pid] * areas[pid][1]
caps = [areas[p][1] for p in FAC_AREAS]
while len(targets) < N_FACULTY:
    targets.append(random.choices(FAC_AREAS, caps)[0])
random.shuffle(targets)
targets = targets[:N_FACULTY]

departs = sorted(random.uniform(0, LAST_DEPART) for _ in targets)

root = ET.Element("routes")
ET.SubElement(root, "vType", id="faculty", vClass="passenger", color="0,0.4,1")

count = skipped = 0
for t, pid in zip(departs, targets):
    edge = areas[pid][0]
    entries = [(e, w) for e, w in zip(ENTRIES, ENTRY_WEIGHTS) if cost(e, edge) is not None]
    exits = [x for x in EXITS if cost(edge, x) is not None]
    if not entries or not exits:
        skipped += 1
        continue
    src = random.choices([e for e, _ in entries], [w for _, w in entries])[0]
    dst = random.choice(exits)
    trip = ET.SubElement(root, "trip", id=f"fac_{count}", type="faculty",
                         depart=f"{t:.1f}", attrib={"from": src, "to": dst})
    stop = ET.SubElement(trip, "stop")
    stop.set("parkingArea", pid)
    stop.set("duration", str(STAY))
    count += 1

os.makedirs(OUT_DIR, exist_ok=True)
ET.indent(root)
ET.ElementTree(root).write(OUT_FILE)
print(count, "faculty vehicles written,", skipped, "skipped. File:", OUT_FILE)

if WRITE_REROUTER:
    add = ET.Element("additional")
    fac_edges = sorted({areas[p][0] for p in FAC_AREAS})
    for n, edge in enumerate(fac_edges):
        costs = []
        for pid in GENERAL:
            if pid in areas:
                c = cost(edge, areas[pid][0])
                if c is not None:
                    costs.append((c, pid))
        costs.sort()
        rr = ET.SubElement(add, "rerouter", id=f"rr_fac_{n}", edges=edge, vTypes="faculty")
        iv = ET.SubElement(rr, "interval", begin="0", end="100000")
        for _, pid in costs[:K]:
            ET.SubElement(iv, "parkingAreaReroute", id=pid, visible="false")
    ET.indent(add)
    ET.ElementTree(add).write(RR_FILE)
    print("Rerouter file:", RR_FILE)