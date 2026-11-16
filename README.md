

Simulation window: 6:00 to 7:00 (3600 s).
Total parking spots: about 630.
Student vehicle pool: about 1500, split across routes 3, 4, and 5.

## Folder layout

```
gradeschool-prototype/
    additional/    gradeschoolarea.add.xml, rerouter files
    map/           png files of the map
    network/       gradeschoolarea.net.xml
    routes/        routes_1 to routes_7 .rou.xml files
    scripts/       makeroute1.py to makeroute7.py, other .py files
    gradeschoolarea.netecfg
    gradeschoolarea.sumocfg
    view.xml
```

Every script uses this line to find the project folder:

```python
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
```

Run scripts from `gradeschool-prototype`, for example `python scripts\makeroute1.py`.

## Landmarks

Entry edges
- 1237202658 (gate 2)
- 360817894#1.24 (close to p4/5, p6, and p7)
- 583962451#0.114 (close to central and p6)

Exit edges
- 205611785 (gate 2.5)
- 313786478#1 (exit to outside campus). This corrects the earlier ID 8384137283, which is not in the network.
- -935386041#0 (towards university road, and an alternative exit). Assumed to also lead to the campus exit.

Parking areas
- School bus loading and unloading (part of p1): pa_2, pa_3 (30 spots each)
- Faculty: pa_7 (24 spots), pa_8 (8), pa_10 (9)
- p1: pa_0, pa_1
- Blue eagle gym: pa_34, pa_35 (small, rarely the first pick)
- p2/p3: pa_15, pa_18, pa_19, pa_20, pa_21
- p4/p5: pa_9, pa_11
- p6: pa_13, pa_36, pa_12, pa_38, pa_14, pa_16, pa_33
- p7: pa_4, pa_5, pa_6, pa_37
- Central: pa_39, pa_22, pa_23, pa_17, pa_24, pa_25, pa_26, pa_27, pa_28, pa_29, pa_30, pa_31, pa_32
- Drop-off areas: pa_40 (5), pa_41 (6), pa_42 (8), pa_44 (3), pa_45 (16). Total 41.

Drop-off lanes
- Near gate 2: 1312076548#0_0, 1312076548#1_0, 30970361#1_0, E0_0
- Near 360817894#1.24 entry: 46522214#1_1
- Near 583962451#0.114 entry: 207134388_0

Behavior notes
- Cars from gate 2 often try p1, p2/p3, and p7 first, but not always.
- Cars from the other two entries often park close to their entry, but not always.
- The gym is rarely the first pick.


## Vehicle colors

| Route | Type | Color value |
|---|---|---|
| 1 | School bus | 1,1,0 (yellow) |
| 2 | Faculty/staff | 0,0.4,1 (blue) |
| 3 | Dropoffs | 0,0.8,0.2 (green) |
| 4 | Parked dropoffs | 1,0.55,0 (orange) |
| 5 | Parking | 0.9,0.1,0.1 (red) |
| 6 | Entry to university road | 0.6,0.2,0.8 (purple) |
| 7 | Campus to exit | 0,0.8,0.8 (cyan) |

## Routes

### Route 1: school bus (makeroute1.py)
- Output: routes/routes_1_school_bus.rou.xml
- 95 buses. Target areas pa_2 and pa_3 (60 spots in total).
- Entry: gate 2 only.
- Exits: 205611785 and 313786478#1, 50% each.
- Departures: spread over 0 to 2400 s.
- Stay: 300 to 900 s (5 to 15 minutes).
- vType: school_bus, vClass passenger, length 5, bus shape.
- Last run: 80 buses written, 0 skipped.
- No rerouter. A bus waits at a full area.

### Route 2: faculty (makeroute2.py)
- Output: routes/routes_2_faculty.rou.xml and additional/rerouter_faculty.add.xml
- 50 vehicles. Target areas pa_7, pa_8, pa_10 (41 spots). The extra 9 reroute to general areas.
- Entries: 60% gate 2, 20% each for the other two.
- Departures: 0 to 1800 s.
- Stay: 100000 s (they never leave). The `to` edge is a placeholder.
- Rerouter: `vTypes="faculty"`, on the faculty edges, with the 5 nearest general areas as candidates.

### Route 3: dropoffs (makeroute3.py)
- Output: routes/routes_3_dropoffs.rou.xml
- 600 vehicles. Stop at one of pa_40 to pa_45 for 15 to 30 s, then exit.
- Entries: 70% gate 2, 15% each for the other two.
- 90% pick an area on a lane near their entry. The rest pick any reachable drop-off area. The pick is weighted by capacity.
- Exits: 205611785 and 313786478#1, 50% each.
- Departures: 0 to 3300 s.
- Rerouter file: scripts\makererouter_dropoff.py writes additional/rerouter_dropoff.add.xml with `vTypes="dropoff"` and the 4 nearest drop-off areas.

### Route 4: parked dropoffs (makeroute4.py)
- Output: routes/routes_4_parked_dropoffs.rou.xml
- 200 vehicles. Park for 300 to 900 s, then exit.
- Entries: 70% gate 2, 15% each for the other two.
- 75% pick a group preferred for their entry. Gate 2 prefers p1, p2/p3, p7. The p4/p5 side entry prefers p4/p5, p6, p7. The central side entry prefers central and p6.
- The other 25% pick any group. The gym has a weight of 0.05.
- Exits: 205611785 and 313786478#1, 50% each.
- Departures: 0 to 3000 s.

### Route 5: parking (makeroute5.py)
- Output: routes/routes_5_parking.rou.xml
- 300 vehicles. Park for 100000 s (never leave).
- Same entries, groups, and preferences as route 4.
- Departures: 0 to 3000 s.
- If general spots fall below about 460, the lots can fill and cars keep searching.

### Route 6: entry to university road (makeroute6.py)
- Output: routes/routes_6_university_road.rou.xml
- 30 vehicles from gate 2 to -935386041#0. No stop.
- Departures: 0 to 3300 s.

### Route 7: campus to exit (makeroute7.py)
- Output: routes/routes_7_campus_exit.rou.xml
- 30 vehicles from 360817894#1.24 and 583962451#0.114 (50% each). No stop.
- Exits: 50% 313786478#1, 25% 205611785, 25% -935386041#0.
- Departures: 1200 to 3500 s (few in the first 20 minutes).

## Config lines

In gradeschoolarea.sumocfg:

```xml
<route-files value="routes/routes_1_school_bus.rou.xml,routes/routes_2_faculty.rou.xml,routes/routes_3_dropoffs.rou.xml,routes/routes_4_parked_dropoffs.rou.xml,routes/routes_5_parking.rou.xml,routes/routes_6_university_road.rou.xml,routes/routes_7_campus_exit.rou.xml"/>
<additional-files value="additional/gradeschoolarea.add.xml,additional/rerouter.add.xml,additional/rerouter_faculty.add.xml,additional/rerouter_dropoff.add.xml"/>
```