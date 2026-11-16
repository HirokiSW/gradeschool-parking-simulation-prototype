import os
import random
import sumolib
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NET = os.path.join(BASE, "network", "gradeschoolarea.net.xml")
OUT_DIR = os.path.join(BASE, "routes")
OUT_FILE = os.path.join(OUT_DIR, "routes_6_university_road.rou.xml")

random.seed(6)
N_VEHICLES = 30
LAST_DEPART = 3300            # seconds

ENTRY = "1237202658"          # gate 2
EXIT = "-935386041#0"         # towards university road

net = sumolib.net.readNet(NET)
for e in (ENTRY, EXIT):
    if not net.hasEdge(e):
        raise SystemExit("Edge not in network: " + e)

path, _ = net.getShortestPath(net.getEdge(ENTRY), net.getEdge(EXIT), vClass="passenger")
if path is None:
    raise SystemExit("No path from gate 2 to the university road exit. Check connections.")
print("Path length:", len(path), "edges")

departs = sorted(random.uniform(0, LAST_DEPART) for _ in range(N_VEHICLES))

root = ET.Element("routes")
ET.SubElement(root, "vType", id="univ_road", vClass="passenger", color="0.6,0.2,0.8")

for i, t in enumerate(departs):
    ET.SubElement(root, "trip", id=f"univ_{i}", type="univ_road",
                  depart=f"{t:.1f}", attrib={"from": ENTRY, "to": EXIT})

os.makedirs(OUT_DIR, exist_ok=True)
ET.indent(root)
ET.ElementTree(root).write(OUT_FILE)
print(N_VEHICLES, "vehicles written. File:", OUT_FILE)