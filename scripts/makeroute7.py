import os
import random
from functools import lru_cache
import sumolib
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NET = os.path.join(BASE, "network", "gradeschoolarea.net.xml")
OUT_DIR = os.path.join(BASE, "routes")
OUT_FILE = os.path.join(OUT_DIR, "routes_7_campus_exit.rou.xml")

random.seed(7)
N_VEHICLES = 30
FIRST_DEPART, LAST_DEPART = 1200, 3500    # seconds, mostly the later part of the hour

ENTRIES = ["360817894#1.24", "583962451#0.114"]
ENTRY_WEIGHTS = [0.5, 0.5]
EXITS = ["313786478#1", "205611785", "-935386041#0"]
EXIT_WEIGHTS = [0.5, 0.25, 0.25]

net = sumolib.net.readNet(NET)
for e in ENTRIES + EXITS:
    if not net.hasEdge(e):
        raise SystemExit("Edge not in network: " + e)

@lru_cache(maxsize=None)
def reachable(a, b):
    path, _ = net.getShortestPath(net.getEdge(a), net.getEdge(b), vClass="passenger")
    return path is not None

for en in ENTRIES:
    print("Entry", en, "reaches:", [x for x in EXITS if reachable(en, x)])

departs = sorted(random.uniform(FIRST_DEPART, LAST_DEPART) for _ in range(N_VEHICLES))

root = ET.Element("routes")
ET.SubElement(root, "vType", id="campus_exit", vClass="passenger", color="0,0.8,0.8")

count = skipped = 0
for t in departs:
    entry = random.choices(ENTRIES, ENTRY_WEIGHTS)[0]
    exits = [(x, w) for x, w in zip(EXITS, EXIT_WEIGHTS) if reachable(entry, x)]
    if not exits:
        skipped += 1
        continue
    dst = random.choices([x for x, _ in exits], [w for _, w in exits])[0]
    ET.SubElement(root, "trip", id=f"exit_{count}", type="campus_exit",
                  depart=f"{t:.1f}", attrib={"from": entry, "to": dst})
    count += 1

os.makedirs(OUT_DIR, exist_ok=True)
ET.indent(root)
ET.ElementTree(root).write(OUT_FILE)
print(count, "vehicles written,", skipped, "skipped. File:", OUT_FILE)